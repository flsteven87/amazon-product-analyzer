import { io, Socket } from 'socket.io-client';
import { WebSocketMessage, ProgressUpdate, AgentStatus } from '@/types';

export class WebSocketService {
  private socket: Socket | null = null;
  private readonly url: string;

  constructor() {
    this.url = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = io(this.url, {
        transports: ['websocket', 'polling'], // Allow fallback to polling
        autoConnect: false,
        timeout: 5000, // 5 second timeout
        forceNew: true, // Force new connection
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        clearTimeout(timeoutId);
        resolve();
      });

      this.socket.on('connect_error', (error) => {
        console.info('📡 WebSocket unavailable, falling back to polling (this is normal if backend is not running)');
        clearTimeout(timeoutId);
        reject(new Error(`WebSocket connection failed: ${error.message}`));
      });

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
      });

      // Add timeout handling
      const timeoutId = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, 6000);

      this.socket.connect();
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Subscribe to task updates
  subscribeToTask(taskId: string): void {
    if (this.socket) {
      this.socket.emit('join_task', { task_id: taskId });
    }
  }

  unsubscribeFromTask(taskId: string): void {
    if (this.socket) {
      this.socket.emit('leave_task', { task_id: taskId });
    }
  }

  // Event listeners
  onProgressUpdate(callback: (update: ProgressUpdate) => void): void {
    if (this.socket) {
      this.socket.on('progress_update', callback);
    }
  }

  onAgentStatus(callback: (status: AgentStatus) => void): void {
    if (this.socket) {
      this.socket.on('agent_status', callback);
    }
  }

  onAnalysisComplete(callback: (data: any) => void): void {
    if (this.socket) {
      this.socket.on('analysis_complete', callback);
    }
  }

  onError(callback: (error: any) => void): void {
    if (this.socket) {
      this.socket.on('error', callback);
    }
  }

  // Remove event listeners
  off(event: string, callback?: (...args: any[]) => void): void {
    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  // Check connection status
  get isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// Singleton instance
export const wsService = new WebSocketService();