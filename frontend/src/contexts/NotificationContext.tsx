import React, { createContext, ReactNode, useContext, useState } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
 
import { AuthContext } from "./AuthContext";
 
const DefaultProps = {
  unreadMessageCount: 0,
  unreadGroupMessageCount: 0,
  connectionStatus: "Uninstantiated"
};
 
export interface NotificationProps {
  unreadMessageCount: number;
  unreadGroupMessageCount: number;
  connectionStatus: string;
}
 
export const NotificationContext = createContext<NotificationProps>(DefaultProps);
 
export const NotificationContextProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useContext(AuthContext);
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);
  const [unreadGroupMessageCount, setUnreadGroupMessageCount] = useState(0);
 
  const { readyState } = useWebSocket(user ? `ws://127.0.0.1:8000/notifications/` : null, {
    queryParams: {
      token: user ? user.token : ""
    },
    onOpen: () => {
      console.log("Connected to Notifications!");
    },
    onClose: () => {
      console.log("Disconnected from Notifications!");
    },
    onMessage: (e) => {
      const data = JSON.parse(e.data);
      switch (data.type) {
        case "unread_count":
            setUnreadMessageCount(data.unread_count)
            break;
        case "unread_group_count":
            setUnreadGroupMessageCount(data.unread_group_count)
            break
        case "new_message_notification":
            setUnreadMessageCount((count) => (count += 1))
            break;
        case "new_message_group_notification":
            setUnreadGroupMessageCount((count) => (count += 1))
            break;
        default:
          console.log("Unknown message type!");
          break;
      }
    }
  });
 
  const connectionStatus = {
    [ReadyState.CONNECTING]: "Connecting",
    [ReadyState.OPEN]: "Open",
    [ReadyState.CLOSING]: "Closing",
    [ReadyState.CLOSED]: "Closed",
    [ReadyState.UNINSTANTIATED]: "Uninstantiated"
  }[readyState];
 
  return (
    <NotificationContext.Provider value={{ unreadMessageCount, unreadGroupMessageCount, connectionStatus }}>
      {children}
    </NotificationContext.Provider>
  );
};