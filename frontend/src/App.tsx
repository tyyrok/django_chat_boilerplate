import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Chat } from "./components/Chat";
import { GroupChat } from "./components/GroupChat"
import { Login } from "./components/Login";
import { Navbar } from "./components/Navbar";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Conversations } from "./components/Conversations";
import { AuthContextProvider } from "./contexts/AuthContext";
import { ActiveConversations } from "./components/ActiveConversations";
import { ActiveGroupConversations } from "./components/ActiveGroupConversations";
import { NotificationContextProvider } from "./contexts/NotificationContext";
 
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
            path="/"
            element={
              <AuthContextProvider>
                <NotificationContextProvider>
                  <Navbar />
                </NotificationContextProvider>
              </AuthContextProvider>
            }
          >
          <Route
            path="conversations/"
            element={
              <ProtectedRoute>
                <ActiveConversations />
              </ProtectedRoute>
            }
          />
          <Route
            path=""
            element={
              <ProtectedRoute>
                <Conversations />
              </ProtectedRoute>
            }
          />
          <Route
            path="/group-conversations/"
            element={
              <ProtectedRoute>
                <ActiveGroupConversations />
              </ProtectedRoute>
            }
          />
          <Route
            path="chats/:conversationName"
            element={
              <ProtectedRoute>
                <Chat />
              </ProtectedRoute>
            }
          />
          <Route
            path="group_chats/:groupConversationName"
            element={
              <ProtectedRoute>
                <GroupChat />
              </ProtectedRoute>
            }
          />
          <Route path="login" element={<Login />} />
        </Route>
          

      </Routes>
    </BrowserRouter>
  );
}