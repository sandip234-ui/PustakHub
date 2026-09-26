/**
 * RealtimeContext — React Context Provider for real-time WebSocket connection.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import useAuth from "../hooks/useAuth";
import realtimeService, { ConnectionStatus } from "../services/realtime.service";

/* eslint-disable react-refresh/only-export-components */
export const RealtimeContext = createContext(null);

export function RealtimeProvider({ children }) {
  const { accessToken, isAuthenticated } = useAuth();
  const [status, setStatus] = useState(realtimeService.status);
  const [lastEvent, setLastEvent] = useState(null);

  // Connect or disconnect when authentication state or token changes
  useEffect(() => {
    if (isAuthenticated && accessToken) {
      realtimeService.connect(accessToken);
    } else {
      realtimeService.disconnect();
    }

    const unsubStatus = realtimeService.onStatusChange(setStatus);
    const unsubEvents = realtimeService.subscribeAll(setLastEvent);

    return () => {
      unsubStatus();
      unsubEvents();
    };
  }, [isAuthenticated, accessToken]);

  const subscribe = useCallback((eventType, callback) => {
    return realtimeService.subscribe(eventType, callback);
  }, []);

  const subscribeMany = useCallback((eventTypes, callback) => {
    return realtimeService.subscribeMany(eventTypes, callback);
  }, []);

  const subscribeAll = useCallback((callback) => {
    return realtimeService.subscribeAll(callback);
  }, []);

  const reconnect = useCallback(() => {
    if (accessToken) {
      realtimeService.connect(accessToken);
    }
  }, [accessToken]);

  const value = useMemo(
    () => ({
      status,
      isConnected: status === ConnectionStatus.CONNECTED,
      isReconnecting: status === ConnectionStatus.RECONNECTING,
      isConnecting: status === ConnectionStatus.CONNECTING,
      lastEvent,
      subscribe,
      subscribeMany,
      subscribeAll,
      reconnect,
    }),
    [status, lastEvent, subscribe, subscribeMany, subscribeAll, reconnect]
  );

  return (
    <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}

export default RealtimeContext;
