import React, { useState, useContext, useEffect, useRef } from "react";
import useWebSocket, { ReadyState } from "react-use-websocket";
import { AuthContext } from "../contexts/AuthContext";
import { useParams, useNavigate } from "react-router-dom";
import { GroupMessageModel } from "../models/GroupMessage";
import { GroupMessage } from "./GroupMessage";
import { GroupConversationModel } from "../models/GroupConversation";
import InfiniteScroll from "react-infinite-scroll-component";
import { ChatLoader } from "./ChatLoader";
import { useHotkeys } from "react-hotkeys-hook";
import { Fragment } from 'react'
import { Menu, Transition } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/20/solid'
import { getUserFriendlyChatName } from "./ActiveGroupConversations";

interface UserResponse {
    username: string;
    name: string;
    url: string;
}
interface MemberResponse {
    username: string;
    first_name: string;
}

export function GroupChat() {
    const [welcomeMessage, setWelcomeMessage] = useState("");
    const [message, setMessage] = useState("");
    const [messageHistory, setMessageHistory] = useState<any>([]);
    const { user } = useContext(AuthContext);
    const { groupConversationName } = useParams();
    const [page, setPage] = useState(2);
    const [hasMoreMessages, setHasMoreMessages] = useState(false);
    const [participants, setParticipants] = useState<string[]>([]);
    const [members, setMembers] = useState<MemberResponse[]>([]);
    const [conversation, setConversation] = useState<GroupConversationModel | null>(null);
    const [meTyping, setMeTyping] = useState(false);
    const timeout = useRef<any>();
    const [typing, setTyping] = useState(false);
    const [users, setUsers] = useState<UserResponse[]>([]);

    function classNames(...classes: any) {
        return classes.filter(Boolean).join(' ')
    }

    const navigate = useNavigate();
    const redirectToChatPath = (path: any) => {
        navigate(`/group_chats/${path}/`);
    };

    function updateTyping(event: { user: string; typing: boolean }) {
        if (event.user !== user!.username) {
            setTyping(event.typing);
        }
    }
    function updateMembers(event: []) {
        const members = event;
        setMembers(event);
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
        user ? `ws://127.0.0.1:8000/group_chats/${groupConversationName}/` : null, {
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
                case "redirect":
                    redirectToChatPath(data.url);
                    break;
                case "chat_message_echo":
                    setMessageHistory((prev: any) => [data.message, ...prev]);
                    sendJsonMessage({ type: "read_messages" });
                    break;
                case "last_50_group_messages":
                    setMessageHistory(data.group_messages);
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
                case "members_list":
                    updateMembers(data.users);
                    break;
                case "typing":
                    updateTyping(data);
                    break;
                default:
                    console.log(data);
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

    function addMember(name: string) {
        sendJsonMessage({
            type: "add_member",
            name: `${name}`,
        });
    }

    function removeMember(name: string) {
        sendJsonMessage({
            type: "remove_member",
            name: `${name}`,
        });
    }

    useEffect(() => {
        async function fetchUsers() {
            const res = await fetch("http://127.0.0.1:8000/api/users/all/", {
                headers: {
                    Authorization: `Token ${user?.token}`,
                },
            });
            const data = await res.json();
            setUsers(data);
        }
        fetchUsers();
    }, [user]);

    useEffect(() => {
        if (connectionStatus === "Open") {
            sendJsonMessage({
                type: "read_group_messages"
            });
        }
    }, [connectionStatus, sendJsonMessage]);

    async function fetchMessages() {
        const apiRes = await fetch(
            `http://127.0.0.1:8000/api/group_messages/?group_conversation=${groupConversationName}&page=${page}`,
            {
                method: "GET",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                    Authorization: `Token ${user?.token}`
                }
            }
        );
        console.log(apiRes.status);
        if (apiRes.status === 200) {
            const data: {
                count: number;
                next: string | null; // URL
                previous: string | null; // URL
                results: GroupMessageModel[];
            } = await apiRes.json();
            console.log(data);
            setHasMoreMessages(data.next !== null);
            setPage(page + 1);
            setMessageHistory((prev: GroupMessageModel[]) => prev.concat(data.results));
        }
    }
    useEffect(() => {
        async function fetchConversation() {
            const apiRes = await fetch(`http://127.0.0.1:8000/api/group_conversations/${groupConversationName}/`, {
                method: "GET",
                headers: {
                    Accept: "application/json",
                    "Content-Type": "application/json",
                    Authorization: `Token ${user?.token}`
                }
            });

            if (apiRes.status === 200) {
                const data: GroupConversationModel = await apiRes.json();
                setConversation(data);
            }
        }
        fetchConversation();
    }, [groupConversationName, user]);
    return (
        <div>
            <span>The WebSocket is currently {connectionStatus}</span>
            {conversation && (
                <div className="py-6">
                    <h3 className="text-xl font-semibold text-gray-900">
                        {getUserFriendlyChatName(conversation?.name)}
                    </h3>
                    <h3 className="text-l font-semibold text-gray-900">
                        Chat admin: {conversation?.admin?.username}
                    </h3>
                    {typing && (
                        <p className="truncate text-sm text-gray-500">typing...</p>
                    )}
                </div>
            )
            }

            <p>{welcomeMessage}</p>
            {user?.username == conversation?.admin.username &&
                <>
                    <Menu as="div" className="relative inline-block text-right mr-2">
                        <Menu.Button className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-5 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
                            Add member
                            <ChevronDownIcon className="-mr-1 h-5 w-5 text-gray-400" aria-hidden="true" />
                        </Menu.Button>

                        <Transition
                            as={Fragment}
                            enter="transition ease-out duration-100"
                            enterFrom="transform opacity-0 scale-95"
                            enterTo="transform opacity-100 scale-100"
                            leave="transition ease-in duration-75"
                            leaveFrom="transform opacity-100 scale-100"
                            leaveTo="transform opacity-0 scale-95"
                        >
                            <Menu.Items className="absolute right-0 z-10 mt-2 w-30 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                                <div className="py-1">
                                    {users.filter((u) => {

                                        if ((u.username != user?.username) && !(members.some((elem) => elem.username == u.username))) {
                                            return u.username
                                        }
                                    })
                                        .map((u) => (
                                            <Menu.Item key={u.username + 2}>
                                                {({ active }) => (
                                                    <a
                                                        key={u.username + 1}
                                                        onClick={() => addMember(u.username)}
                                                        className={classNames(
                                                            active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                                                            'block px-4 py-2 text-sm'
                                                        )}
                                                    >
                                                        {u.username}
                                                    </a>
                                                )}
                                            </Menu.Item>
                                        ))}
                                </div>
                            </Menu.Items>
                        </Transition>
                    </Menu>
                    <Menu as="div" className="relative inline-block text-right">
                        <Menu.Button className="inline-flex w-full justify-center gap-x-1.5 rounded-md bg-white px-5 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
                            Remove member
                            <ChevronDownIcon className="-mr-1 h-5 w-5 text-gray-400" aria-hidden="true" />
                        </Menu.Button>

                        <Transition
                            as={Fragment}
                            enter="transition ease-out duration-100"
                            enterFrom="transform opacity-0 scale-95"
                            enterTo="transform opacity-100 scale-100"
                            leave="transition ease-in duration-75"
                            leaveFrom="transform opacity-100 scale-100"
                            leaveTo="transform opacity-0 scale-95"
                        >
                            <Menu.Items className="absolute right-0 z-10 mt-2 w-30 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                                <div className="py-1">
                                    {members.filter((u) => u.username != user?.username)
                                        .map((u) => (
                                            <Menu.Item key={u.username + 2}>
                                                {({ active }) => (
                                                    <a
                                                        key={u.username + 1}
                                                        onClick={() => removeMember(u.username)}
                                                        className={classNames(
                                                            active ? 'bg-gray-100 text-gray-900' : 'text-gray-700',
                                                            'block px-4 py-2 text-sm'
                                                        )}
                                                    >
                                                        {u.username}
                                                    </a>
                                                )}
                                            </Menu.Item>
                                        ))}
                                </div>
                            </Menu.Items>
                        </Transition>
                    </Menu>
                </>
            }
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
            <div className="flex flex-row h-[20rem]">
                <div className="basis-2/12 pl-3 mt-3 rounded-md border border-gray-200 p-2 overflow-y-scroll">
                    <p>Users:</p>
                    <div className="py1 decoration-solid underline text-green-700">
                        {user?.username}
                    </div>
                    <p className="mt-2">Online:</p>
                    {participants.filter((u) => u != user?.username)
                        .map((u) => (
                            <div key={u+3} className="py1 text-green-600">
                                {u}
                            </div>
                        ))}
                    <p className="mt-2">Offline:</p>
                    {members.filter((u) => {
                        if (!(participants.some((elem) => elem == u.username))) {
                            return u.username
                        }
                    })
                        .map((u) => (
                            <div key={u.username + 4} className="py1">
                                {u.username}
                            </div>
                        ))}

                </div>
                <div
                    id="scrollableDiv"
                    className="basis-10/12 mt-3 flex flex-col-reverse w-full rounded-md border border-gray-200 p-6 overflow-y-scroll"
                >
                    <div>
                        {/* Put the scroll bar always on the bottom */}
                        <InfiniteScroll
                            dataLength={messageHistory?.length}
                            next={fetchMessages}
                            className="flex flex-col-reverse" // To put endMessage and loader to the top
                            inverse={true}
                            hasMore={hasMoreMessages}
                            loader={<ChatLoader />}
                            scrollableTarget="scrollableDiv"
                        >
                            {messageHistory?.map((message: GroupMessageModel) => (
                                <GroupMessage key={message?.id} message={message} />
                            ))}
                        </InfiniteScroll>
                    </div>
                </div>
            </div>
        </div>
    );
}