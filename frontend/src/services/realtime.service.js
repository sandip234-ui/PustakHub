/**
 * Real-time WebSocket Client for PustakHub.
 *
 * Manages WebSocket lifecycle, authentication, bounded exponential reconnects,
 * heartbeat ping/pong, and event subscription fan-out.
 */

export const ConnectionStatus = {
  CONNECTED: "CONNECTED",
  CONNECTING: "CONNECTING",
  RECONNECTING: "RECONNECTING",
  DISCONNECTED: "DISCONNECTED",
};

export const RealtimeEventType = {
  // Catalog Events
  CATEGORY_CREATED: "CATEGORY_CREATED",
  CATEGORY_UPDATED: "CATEGORY_UPDATED",
  CATEGORY_DELETED: "CATEGORY_DELETED",
  BOOK_CREATED: "BOOK_CREATED",
  BOOK_UPDATED: "BOOK_UPDATED",
  BOOK_DELETED: "BOOK_DELETED",
  COPY_CREATED: "COPY_CREATED",
  COPY_UPDATED: "COPY_UPDATED",
  COPY_DELETED: "COPY_DELETED",

  // Circulation Events
  COPY_ISSUED: "COPY_ISSUED",
  COPY_RETURNED: "COPY_RETURNED",
  FINE_ISSUED: "FINE_ISSUED",
  FINE_PAID: "FINE_PAID",
  FINE_WAIVED: "FINE_WAIVED",

  // IAM Events
  USER_CREATED: "USER_CREATED",
  USER_UPDATED: "USER_UPDATED",
  USER_SUSPENDED: "USER_SUSPENDED",
  USER_DEACTIVATED: "USER_DEACTIVATED",
  ROLE_ASSIGNED: "ROLE_ASSIGNED",
  ROLE_REVOKED: "ROLE_REVOKED",

  // Audit Events
  AUDIT_EVENT_CREATED: "AUDIT_EVENT_CREATED",

  // System & Connection Events
  SYSTEM_RECONNECTED: "SYSTEM_RECONNECTED",
  SYSTEM_NOTIFICATION: "SYSTEM_NOTIFICATION",
};

class RealtimeClient {
  constructor() {
    this.socket = null;
    this.status = ConnectionStatus.DISCONNECTED;
    this.token = null;
    this.retryCount = 0;
    this.maxRetries = 10;
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.listeners = new Map(); // eventType -> Set<callback>
    this.allListeners = new Set(); // wildcard callback for all events
    this.statusListeners = new Set(); // status callback
    this.lastEvent = null;
    this.wasReconnected = false;
  }

  getWebSocketUrl(token) {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    let wsUrl;
    if (apiUrl.startsWith("http://")) {
      wsUrl = apiUrl.replace("http://", "ws://");
    } else if (apiUrl.startsWith("https://")) {
      wsUrl = apiUrl.replace("https://", "wss://");
    } else if (apiUrl.startsWith("/")) {
      const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
      wsUrl = `${proto}//${window.location.host}${apiUrl}`;
    } else {
      wsUrl = `ws://${apiUrl}`;
    }

    wsUrl = wsUrl.replace(/\/+$/, "");
    if (wsUrl.endsWith("/api/v1")) {
      wsUrl = `${wsUrl}/realtime/ws`;
    } else if (wsUrl.endsWith("/api")) {
      wsUrl = `${wsUrl}/v1/realtime/ws`;
    } else if (!wsUrl.includes("/realtime/ws")) {
      wsUrl = `${wsUrl}/realtime/ws`;
    }

    return `${wsUrl}?token=${encodeURIComponent(token)}`;
  }

  setStatus(newStatus) {
    if (this.status !== newStatus) {
      this.status = newStatus;
      this.statusListeners.forEach((callback) => {
        try {
          callback(newStatus);
        } catch {
          // Ignore listener errors
        }
      });
    }
  }

  connect(token) {
    if (!token) {
      this.disconnect();
      return;
    }

    // If already connected with same token, do nothing
    if (
      this.token === token &&
      (this.status === ConnectionStatus.CONNECTED ||
        this.status === ConnectionStatus.CONNECTING)
    ) {
      return;
    }

    this.disconnect();
    this.token = token;
    this.setStatus(
      this.retryCount > 0
        ? ConnectionStatus.RECONNECTING
        : ConnectionStatus.CONNECTING
    );

    try {
      const url = this.getWebSocketUrl(token);
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        const previouslyDisconnected = this.retryCount > 0;
        this.retryCount = 0;
        this.setStatus(ConnectionStatus.CONNECTED);
        this.startHeartbeat();

        if (previouslyDisconnected) {
          this.wasReconnected = true;
          // Notify listeners of reconnection so they can refetch authoritative REST state
          this.notify({
            type: "SYSTEM_RECONNECTED",
            timestamp: new Date().toISOString(),
          });
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === "PONG") return;

          this.lastEvent = payload;
          this.notify(payload);
        } catch {
          // Ignore parse errors on malformed messages
        }
      };

      this.socket.onerror = () => {
        // Handled in onclose
      };

      this.socket.onclose = (event) => {
        this.stopHeartbeat();
        this.socket = null;

        // If closed intentionally or unauthorized (e.g. 1008 policy violation / invalid token)
        if (event.code === 1008 || event.code === 4401 || !this.token) {
          this.setStatus(ConnectionStatus.DISCONNECTED);
          return;
        }

        // Otherwise schedule bounded reconnect with exponential backoff
        this.setStatus(ConnectionStatus.RECONNECTING);
        this.scheduleReconnect();
      };
    } catch {
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.retryCount >= this.maxRetries) {
      this.setStatus(ConnectionStatus.DISCONNECTED);
      return;
    }

    // Exponential backoff: 1s, 2.25s, 3.37s, up to max 30s
    const delay = Math.min(
      1000 * Math.pow(1.5, this.retryCount) + Math.random() * 500,
      30000
    );
    this.retryCount += 1;

    this.reconnectTimer = setTimeout(() => {
      if (this.token) {
        this.connect(this.token);
      }
    }, delay);
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        try {
          this.socket.send(JSON.stringify({ type: "PING" }));
        } catch {
          // Socket might have closed
        }
      }
    }, 25000);
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopHeartbeat();
    this.token = null;
    this.retryCount = 0;

    if (this.socket) {
      try {
        this.socket.close(1000, "Normal Closure");
      } catch {
        // Ignore close error
      }
      this.socket = null;
    }

    this.setStatus(ConnectionStatus.DISCONNECTED);
  }

  subscribe(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);

    return () => {
      const set = this.listeners.get(eventType);
      if (set) {
        set.delete(callback);
        if (set.size === 0) {
          this.listeners.delete(eventType);
        }
      }
    };
  }

  subscribeMany(eventTypes, callback) {
    if (!Array.isArray(eventTypes)) {
      return () => {};
    }
    const unsubs = eventTypes.map((eventType) => this.subscribe(eventType, callback));
    return () => {
      unsubs.forEach((unsub) => {
        if (typeof unsub === "function") {
          unsub();
        }
      });
    };
  }

  subscribeAll(callback) {
    this.allListeners.add(callback);
    return () => {
      this.allListeners.delete(callback);
    };
  }

  onStatusChange(callback) {
    this.statusListeners.add(callback);
    callback(this.status);
    return () => {
      this.statusListeners.delete(callback);
    };
  }

  notify(event) {
    // Notify specific type subscribers
    const typeListeners = this.listeners.get(event.type);
    if (typeListeners) {
      typeListeners.forEach((cb) => {
        try {
          cb(event);
        } catch {
          // Guard against subscriber errors
        }
      });
    }

    // Notify wildcard subscribers
    this.allListeners.forEach((cb) => {
      try {
        cb(event);
      } catch {
        // Guard against wildcard errors
      }
    });
  }
}

export const realtimeService = new RealtimeClient();
export default realtimeService;
