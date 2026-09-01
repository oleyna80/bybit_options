"""
WebSocket Manager for real-time portfolio updates broadcast
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from bybit_options.models import PortfolioRiskModel, PositionModel, MarginModel

logger = logging.getLogger(__name__)


class ConnectionStatus(str, Enum):
    """WebSocket connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ClientInfo:
    """Information about connected client"""
    websocket: WebSocket
    client_id: str
    connected_at: datetime
    last_message_at: Optional[datetime] = None
    subscriptions: Set[str] = field(default_factory=set)
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "client_id": self.client_id,
            "connected_at": self.connected_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "subscriptions": list(self.subscriptions),
            "status": self.status.value
        }


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts portfolio updates
    
    Features:
    - Multiple client connections
    - Automatic disconnect handling
    - Broadcast updates to all connected clients
    - Connection health monitoring
    - Subscription management
    """
    
    def __init__(self, broadcast_interval: float = 5.0):
        """
        Args:
            broadcast_interval: Interval between broadcast updates in seconds (default: 5.0)
        """
        self.active_connections: Set[WebSocket] = set()
        self.clients: Dict[str, ClientInfo] = {}
        self.broadcast_interval = broadcast_interval
        self._broadcast_task: Optional[asyncio.Task] = None
        self._is_running = False
        
        # Latest portfolio data for broadcasting
        self._latest_portfolio: Optional[PortfolioRiskModel] = None
        self._latest_portfolio_timestamp: Optional[datetime] = None
        
        # Latest options board data for broadcasting
        self._latest_options: Optional[dict] = None
        self._latest_options_timestamp: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_disconnections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "last_broadcast": None,
            "last_options_broadcast": None
        }
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: FastAPI WebSocket object
            
        Returns:
            Client ID for the connection
        """
        await websocket.accept()
        
        # Generate unique client ID
        client_id = str(uuid.uuid4())[:8]
        
        # Create client info
        client_info = ClientInfo(
            websocket=websocket,
            client_id=client_id,
            connected_at=datetime.utcnow(),
            subscriptions={"portfolio"}  # Default subscription
        )
        
        # Store connection
        self.active_connections.add(websocket)
        self.clients[client_id] = client_info
        
        # Update stats
        self.stats["total_connections"] += 1
        
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Send welcome message
        await self._send_to_client(
            client_id,
            {
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Connected to portfolio WebSocket",
                "subscriptions": list(client_info.subscriptions)
            }
        )
        
        return client_id
    
    async def disconnect(self, client_id: str, code: int = 1000, reason: str = "Normal closure"):
        """
        Disconnect a specific client
        
        Args:
            client_id: Client ID to disconnect
            code: WebSocket close code
            reason: Close reason
        """
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        
        try:
            await client_info.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.warning(f"Error closing WebSocket for client {client_id}: {e}")
        
        # Remove from active connections
        if client_info.websocket in self.active_connections:
            self.active_connections.remove(client_info.websocket)
        
        # Update client status
        client_info.status = ConnectionStatus.DISCONNECTED
        
        # Update stats
        self.stats["total_disconnections"] += 1
        
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def handle_client(self, client_id: str):
        """
        Handle messages from a specific client
        
        Args:
            client_id: Client ID to handle
        """
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        
        try:
            while True:
                # Receive message from client
                message = await client_info.websocket.receive_text()
                self.stats["total_messages_received"] += 1
                client_info.last_message_at = datetime.utcnow()
                
                # Process message
                await self._process_client_message(client_id, message)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket client {client_id} disconnected normally")
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            await self.disconnect(client_id, code=1011, reason=str(e))
    
    async def _process_client_message(self, client_id: str, message: str):
        """
        Process incoming message from client
        
        Args:
            client_id: Client ID
            message: JSON message string
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Subscribe to specific data types
                subscriptions = data.get("subscriptions", [])
                await self._update_subscriptions(client_id, subscriptions)
                
            elif message_type == "unsubscribe":
                # Unsubscribe from specific data types
                subscriptions = data.get("subscriptions", [])
                await self._remove_subscriptions(client_id, subscriptions)
                
            elif message_type == "ping":
                # Respond to ping
                await self._send_to_client(
                    client_id,
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
            elif message_type == "request_portfolio":
                # Send latest portfolio data
                await self._send_latest_portfolio(client_id)
                
            else:
                logger.warning(f"Unknown message type from client {client_id}: {message_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from client {client_id}: {message}")
        except Exception as e:
            logger.error(f"Error processing message from client {client_id}: {e}")
    
    async def _update_subscriptions(self, client_id: str, subscriptions: List[str]):
        """Update client subscriptions"""
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        client_info.subscriptions.update(subscriptions)
        
        await self._send_to_client(
            client_id,
            {
                "type": "subscription_updated",
                "subscriptions": list(client_info.subscriptions),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _remove_subscriptions(self, client_id: str, subscriptions: List[str]):
        """Remove client subscriptions"""
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        client_info.subscriptions.difference_update(subscriptions)
        
        await self._send_to_client(
            client_id,
            {
                "type": "subscription_updated",
                "subscriptions": list(client_info.subscriptions),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _send_latest_portfolio(self, client_id: str):
        """Send latest portfolio data to specific client"""
        if not self._latest_portfolio:
            await self._send_to_client(
                client_id,
                {
                    "type": "error",
                    "message": "No portfolio data available",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            return
        
        await self._send_portfolio_update(client_id, self._latest_portfolio)
    
    async def broadcast_portfolio_update(self, portfolio: PortfolioRiskModel):
        """
        Broadcast portfolio update to all connected clients
        
        Args:
            portfolio: PortfolioRiskModel to broadcast
        """
        self._latest_portfolio = portfolio
        self._latest_portfolio_timestamp = datetime.utcnow()
        
        # Prepare update message
        message = self._prepare_portfolio_message(portfolio)
        
        # Broadcast to all clients with portfolio subscription
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            if "portfolio" in client_info.subscriptions and client_info.status == ConnectionStatus.CONNECTED:
                try:
                    await client_info.websocket.send_json(message)
                    self.stats["total_messages_sent"] += 1
                except Exception as e:
                    logger.warning(f"Failed to send to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id, code=1001, reason="Send failed")
        
        # Update stats
        self.stats["last_broadcast"] = datetime.utcnow().isoformat()
    
    async def broadcast_options_board_update(self, options_data: dict):
        """
        Broadcast options board update to all connected clients
        
        Args:
            options_data: Dictionary with options board data
        """
        self._latest_options = options_data
        self._latest_options_timestamp = datetime.utcnow()
        
        # Prepare update message
        message = {
            "type": "options_board_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": options_data
        }
        
        # Broadcast to all clients with options subscription
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            if "options" in client_info.subscriptions and client_info.status == ConnectionStatus.CONNECTED:
                try:
                    await client_info.websocket.send_json(message)
                    self.stats["total_messages_sent"] += 1
                except Exception as e:
                    logger.warning(f"Failed to send to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id, code=1001, reason="Send failed")
        
        # Update stats
        self.stats["last_options_broadcast"] = datetime.utcnow().isoformat()
    
    async def _send_portfolio_update(self, client_id: str, portfolio: PortfolioRiskModel):
        """Send portfolio update to specific client"""
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        
        if client_info.status != ConnectionStatus.CONNECTED:
            return
        
        message = self._prepare_portfolio_message(portfolio)
        
        try:
            await client_info.websocket.send_json(message)
            self.stats["total_messages_sent"] += 1
        except Exception as e:
            logger.warning(f"Failed to send portfolio to client {client_id}: {e}")
            await self.disconnect(client_id, code=1001, reason="Send failed")
    
    def _prepare_portfolio_message(self, portfolio: PortfolioRiskModel) -> Dict[str, Any]:
        """Prepare portfolio data for WebSocket message"""
        # Convert portfolio to dict
        portfolio_dict = portfolio.dict()
        
        # Add metadata
        return {
            "type": "portfolio_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": portfolio_dict
        }
    
    async def _send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        
        if client_info.status != ConnectionStatus.CONNECTED:
            return
        
        try:
            await client_info.websocket.send_json(message)
            self.stats["total_messages_sent"] += 1
        except Exception as e:
            logger.warning(f"Failed to send to client {client_id}: {e}")
            await self.disconnect(client_id, code=1001, reason="Send failed")
    
    async def start_broadcast_loop(self, portfolio_provider: callable):
        """
        Start automatic broadcast loop
        
        Args:
            portfolio_provider: Async function that returns PortfolioRiskModel
        """
        self._is_running = True
        
        while self._is_running:
            try:
                # Get latest portfolio data
                portfolio = await portfolio_provider()
                
                if portfolio:
                    # Broadcast to all clients
                    await self.broadcast_portfolio_update(portfolio)
                
                # Wait for next broadcast
                await asyncio.sleep(self.broadcast_interval)
                
            except asyncio.CancelledError:
                logger.info("Broadcast loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(self.broadcast_interval)  # Continue despite errors
    
    def stop_broadcast_loop(self):
        """Stop the broadcast loop"""
        self._is_running = False
        
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self.stats,
            "active_connections": len(self.active_connections),
            "total_clients": len(self.clients),
            "latest_portfolio_timestamp": (
                self._latest_portfolio_timestamp.isoformat()
                if self._latest_portfolio_timestamp else None
            ),
            "latest_options_timestamp": (
                self._latest_options_timestamp.isoformat()
                if self._latest_options_timestamp else None
            ),
            "broadcast_interval": self.broadcast_interval,
            "is_running": self._is_running
        }
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific client"""
        if client_id not in self.clients:
            return None
        
        return self.clients[client_id].to_dict()
    
    def get_all_clients_info(self) -> List[Dict[str, Any]]:
        """Get information about all clients"""
        return [client.to_dict() for client in self.clients.values()]
    
    async def cleanup_disconnected(self):
        """Clean up disconnected clients"""
        disconnected_clients = []
        
        for client_id, client_info in self.clients.items():
            if client_info.status == ConnectionStatus.DISCONNECTED:
                disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            del self.clients[client_id]
        
        if disconnected_clients:
            logger.info(f"Cleaned up {len(disconnected_clients)} disconnected clients")


# Singleton instance for easy access
_global_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create global WebSocket manager instance"""
    global _global_ws_manager
    
    if _global_ws_manager is None:
        _global_ws_manager = WebSocketManager()
    
    return _global_ws_manager


if __name__ == "__main__":
    # Test the WebSocket manager
    import sys
    sys.path.append(".")
    
    from bybit_options.models import PortfolioRiskModel, MarginModel, CoinRiskModel, GreeksModel
    
    # Create test portfolio
    test_portfolio = PortfolioRiskModel(
        margin=MarginModel(
            account_type="UNIFIED",
            total_equity=50000.0,
            available_balance=25000.0,
            used_margin=25000.0,
            margin_ratio=50.0
        ),
        coin_risks={
            "BTC": CoinRiskModel(
                base_coin="BTC",
                total_greeks=GreeksModel(
                    delta_coin=0.5234,
                    gamma_coin=0.000123,
                    vega_usd=145.67,
                    theta_usd=-23.45
                ),
                underlying_price=95000.0
            )
        },
        total_vega_usd=145.67,
        total_theta_usd=-23.45
    )
    
    # Test message preparation
    manager = WebSocketManager()
    message = manager._prepare_portfolio_message(test_portfolio)
    
    print("WebSocket Manager Test")
    print(f"Message type: {message['type']}")
    print(f"Message timestamp: {message['timestamp']}")
    print(f"Has portfolio data: {'data' in message}")
    
    # Test stats
    stats = manager.get_connection_stats()
    print(f"\nInitial stats: {stats}")