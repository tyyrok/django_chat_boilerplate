import { useContext, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { AuthContext } from "../contexts/AuthContext";
import { GroupConversationModel } from "../models/GroupConversation";

export function ActiveGroupConversations() {
    const { user } = useContext(AuthContext);
    const [conversations, setActiveGroupConversations] = useState<GroupConversationModel[]>([]);

    useEffect(() => {
        async function fetchUsers() {
            const res = await fetch("http://127.0.0.1:8000/api/group_conversations/", {
                headers: {
                    Authorization: `Token ${user?.token}`
                }
            });
            const data = await res.json();
            setActiveGroupConversations(data);
        }
        fetchUsers();
    }, [user]);


    function formatMessageTimestamp(timestamp?: string) {
        if (!timestamp) return;
        const date = new Date(timestamp);
        return date.toLocaleTimeString().slice(0, 5);
    }

    const navigate = useNavigate();
    const navigateNewGroupChat = () => {
        navigate('/group_chats/new');
    };

    return (
        <div>
            <div className="mb-3">
                <button className="ml-3 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 px-3 py-1" onClick={navigateNewGroupChat}>
                    Add group chat
                </button>
            </div>
            <div>
                {conversations.map((c) => (
                        <Link
                            to={`/group_chats/${c.name}`}
                            key={c.name}
                        >
                            <div className="border border-gray-200 w-full p-3">
                                <h3 className="text-xl font-semibold text-gray-800">{getUserFriendlyChatName(c.name)}</h3>
                                <div className="flex justify-between">
                                    <p className="text-gray-700">{c.last_message?.content}</p>
                                    <p className="text-gray-700">{formatMessageTimestamp(c.last_message?.timestamp)}</p>
                                </div>
                            </div>
                        </Link>
                ))}
            </div>
        </div>
    );
}

export function getUserFriendlyChatName(name: string) {
    const list = name.split('__');
    return `Group chat with ${list[1]} (${list[2]})`
}