/**
 * useRealtime — custom React hook to access real-time WebSocket state and subscriptions.
 */

import { useContext } from "react";
import { RealtimeContext } from "../context/RealtimeContext";

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error("useRealtime must be used within a RealtimeProvider");
  }
  return context;
}

export default useRealtime;
