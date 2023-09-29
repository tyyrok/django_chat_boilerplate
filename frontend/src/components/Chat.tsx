import React, { useState, useContext, useEffect, useRef } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { AuthContext } from "../contexts/AuthContext";
import { useParams } from "react-router-dom";
import { MessageModel } from "../models/Message";
import { Message } from "./Message";
import { ConversationModel } from "../models/Conversation";
import InfiniteScroll from "react-infinite-scroll-component";
import { ChatLoader } from "./ChatLoader";
import { useHotkeys } from "react-hotkeys-hook";
 
export function Chat() {
  const [welcomeMessage, setWelcomeMessage] = useState("");
  const [message, setMessage] = useState("");
  const [messageHistory, setMessageHistory] = useState<any>([]);
  const { user } = useContext(AuthContext);
  const { conversationName } = useParams();
  const [page, setPage] = useState(2);
  const [hasMoreMessages, setHasMoreMessages] = useState(false);
  const [participants, setParticipants] = useState<string[]>([]);
  const [conversation, setConversation] = useState<ConversationModel | null>(null);
  const [meTyping, setMeTyping] = useState(false);
  const timeout = useRef<any>();
  const [typing, setTyping] = useState(false);

  function updateTyping(event: { user: string; typing: boolean }) {
    if (event.user !== user!.username) {
      setTyping(event.typing);
    }
  }

  function timeoutFunction() {
    setMeTyping(false);
    sendJsonMessage({ type: "typing", typing: false });
  }

  function onType() {
    if (meTyping === false) {
      setMeTyping(true);
      sendJsonMessage({ type: "typing", typing: true });
      timeout.current = setTimeout(timeoutFunction, 5000);
    } else {
      clearTimeout(timeout.current);
      timeout.current = setTimeout(timeoutFunction, 5000);
    }
  }

  useEffect(() => () => clearTimeout(timeout.current), []);

  const inputReference: any = useHotkeys(
    "enter",
    () => {
      handleSubmit();
    },
    {
      enableOnTags: ["INPUT"]
    }
  );

  useEffect(() => {
    (inputReference.current as HTMLElement).focus();
  }, [inputReference]);

  const { readyState, sendJsonMessage } = useWebSocket(
      user ? `ws://127.0.0.1:8000/chats/${conversationName}/`: null, {
    queryParams: {
      token: user ? user.token : "",
    },
    onOpen: () => {
      console.log("Connected!");
    },
    onClose: () => {
      console.log("Disconnected!");
    },
    onMessage: (e) => {
      const data = JSON.parse(e.data);
      switch (data.type) {
        case "welcome_message":
          setWelcomeMessage(data.message);
          console.log(data.message);
          break;
        case "chat_message_echo":
          setMessageHistory((prev:any) => [data.message, ...prev]);
          sendJsonMessage({ type: "read_messages" });
          break;
        case "last_50_messages":
          setMessageHistory(data.messages);
          setHasMoreMessages(data.has_more);
          break;
        case "user_join":
          setParticipants((pcpts: string[]) => {
            if (!pcpts.includes(data.user)) {
              return [...pcpts, data.user];
            }
            return pcpts;
          });
          break;
        case "user_leave":
          setParticipants((pcpts: string[]) => {
            const newPcpts = pcpts.filter((x) => x !== data.user);
            return newPcpts;
          });
          break;
        case "online_user_list":
          setParticipants(data.users);
          break;
        case "typing":
          updateTyping(data);
          break;
        default:
          console.log("Unknown message type!");
          break;
      }
    },
    
  });

  function handleChangeMessage(e: any) {
    setMessage(e.target.value);
    onType();
  }
  function handleSubmit() {
    if (message.length === 0) return;
    if (message.length > 512) return;
    sendJsonMessage({
      type: "chat_message",
      message,
    });
    setMessage("");
    clearTimeout(timeout.current);
    timeoutFunction();
  }
 
  const connectionStatus = {
    [ReadyState.CONNECTING]: "Connecting",
    [ReadyState.OPEN]: "Open",
    [ReadyState.CLOSING]: "Closing",
    [ReadyState.CLOSED]: "Closed",
    [ReadyState.UNINSTANTIATED]: "Uninstantiated"
  }[readyState];

  useEffect(() => {
    if (connectionStatus === "Open") {
      sendJsonMessage({
        type: "read_messages"
      });
    }
  }, [connectionStatus, sendJsonMessage]);

  async function fetchMessages() {
    const apiRes = await fetch(
      `http://127.0.0.1:8000/api/messages/?conversation=${conversationName}&page=${page}`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Token ${user?.token}`
        }
      }
    );
    if (apiRes.status === 200) {
      const data: {
        count: number;
        next: string | null; // URL
        previous: string | null; // URL
        results: MessageModel[];
      } = await apiRes.json();
      setHasMoreMessages(data.next !== null);
      setPage(page + 1);
      setMessageHistory((prev: MessageModel[]) => prev.concat(data.results));
    }
  }

  useEffect(() => {
    async function fetchConversation() {
      const apiRes = await fetch(`http://127.0.0.1:8000/api/conversations/${conversationName}/`, {
        method: "GET",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          Authorization: `Token ${user?.token}`
        }
      });
      if (apiRes.status === 200) {
        const data: ConversationModel = await apiRes.json();
        setConversation(data);
      }
    }
    fetchConversation();
  }, [conversationName, user]);
 
  return (
    <div>
      <span>The WebSocket is currently {connectionStatus}</span>
      {conversation && (
          <div className="py-6">
            <h3 className="text-3xl font-semibold text-gray-900">
              Chat with user: {conversation.other_user.username}
            </h3>
            <span className="text-sm">
              {conversation.other_user.username} is currently
              {participants.includes(conversation.other_user.username) ? " online" : " offline"}
            </span>
            {typing && (
              <p className="truncate text-sm text-gray-500">typing...</p>
            )}
          </div>
        )
      }
    
      <p>{welcomeMessage}</p>
      <div className="flex w-full items-center justify-between rounded-md border border-gray-200 p-3">
        <input
          type="text"
          placeholder="   Message"
          className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
          name="message"
          value={message}
          onChange={handleChangeMessage}
          required
          ref={inputReference}
          maxLength={511}
        />
        <button className="ml-3 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 px-3 py-1" onClick={handleSubmit}>
          Submit
        </button>
      </div>
      <hr />
      <div
        id="scrollableDiv"
        className="h-[20rem] mt-3 flex flex-col-reverse relative w-full rounded-md border border-gray-200 p-6 overflow-y-scroll"
      >
        <div>
          {/* Put the scroll bar always on the bottom */}
          <InfiniteScroll
            dataLength={messageHistory.length}
            next={fetchMessages}
            className="flex flex-col-reverse" // To put endMessage and loader to the top
            inverse={true}
            hasMore={hasMoreMessages}
            loader={<ChatLoader />}
            scrollableTarget="scrollableDiv"
          >
            {messageHistory.map((message: MessageModel) => (
              <Message key={message.id} message={message} />
            ))}
          </InfiniteScroll>
        </div>
      </div>
    </div>
  );
}