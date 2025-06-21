import { ProgressUpdate, AgentStatus } from '@/types';

export class NativeWebSocketService {
  private socket: WebSocket | null = null;
  private readonly url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private eventHandlers: Map<string, Function[]> = new Map();

  constructor() {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';
    // Convert HTTP URL to WebSocket URL
    if (baseUrl.startsWith('http://')) {
      this.url = baseUrl.replace('http://', 'ws://') + '/api/v1/websocket/ws';
    } else if (baseUrl.startsWith('https://')) {
      this.url = baseUrl.replace('https://', 'wss://') + '/api/v1/websocket/ws';
    } else {
      this.url = 'ws://localhost:8000/api/v1/websocket/ws';
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = new WebSocket(this.url);
        
        const timeout = setTimeout(() => {
          if (this.socket && this.socket.readyState !== WebSocket.OPEN) {
            this.socket.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);

        this.socket.onopen = () => {
          clearTimeout(timeout);
          console.log('✅ WebSocket connected successfully');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.socket.onerror = (error) => {
          clearTimeout(timeout);
          console.info('📡 WebSocket unavailable, falling back to polling');
          reject(new Error('WebSocket connection failed'));
        };

        this.socket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        this.socket.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          
          // Trigger error handlers to notify components
          const errorHandlers = this.eventHandlers.get('error') || [];
          errorHandlers.forEach(handler => {
            handler({ type: 'connection_lost', reason: event.reason });
          });
          
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
              this.connect().catch(() => {
                // Ignore reconnection failures
              });
            }, 2000);
          } else {
            console.info('Max reconnection attempts reached, switching to polling');
          }
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  // Subscribe to task updates
  subscribeToTask(taskId: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'join_task',
        task_id: taskId
      }));
    }
  }

  unsubscribeFromTask(taskId: string): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({
        type: 'leave_task',
        task_id: taskId
      }));
    }
  }

  // Event listeners
  onProgressUpdate(callback: (update: ProgressUpdate) => void): void {
    this.addEventHandler('progress_update', callback);
  }

  onAgentStatus(callback: (status: AgentStatus) => void): void {
    this.addEventHandler('agent_status', callback);
  }

  onAnalysisComplete(callback: (data: any) => void): void {
    this.addEventHandler('analysis_complete', callback);
  }

  onError(callback: (error: any) => void): void {
    this.addEventHandler('error', callback);
  }

  // Remove event listeners
  off(event: string, callback?: (...args: any[]) => void): void {
    if (callback) {
      const handlers = this.eventHandlers.get(event) || [];
      const index = handlers.indexOf(callback);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      this.eventHandlers.delete(event);
    }
  }

  // Check connection status
  get isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  private addEventHandler(event: string, callback: Function): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(callback);
  }

  private handleMessage(message: any): void {
    const handlers = this.eventHandlers.get(message.type) || [];
    handlers.forEach(handler => {
      try {
        handler(message);
      } catch (e) {
        console.error('Error in WebSocket event handler:', e);
      }
    });
  }
}

// Export singleton instance
export const wsService = new NativeWebSocketService();