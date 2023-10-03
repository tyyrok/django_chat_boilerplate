import { useContext } from "react";

import { AuthContext } from "../contexts/AuthContext";
import { GroupMessageModel } from "../models/GroupMessage";

export function classNames(...classes: any) {
    return classes.filter(Boolean).join(" ");
}

export function GroupMessage({ message }: { message: GroupMessageModel }) {
    const { user } = useContext(AuthContext);

    function formatMessageTimestamp(timestamp: string) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString().slice(0, 5);
    }

    return (
        <li
            className={classNames(
                "mt-1 mb-1 flex",
                user!.username !== message.from_user.username ? "justify-start" : "justify-end"
            )}
        >
            <div
                className={classNames(
                    "relative max-w-xl rounded-lg px-2 py-1 text-gray-700 shadow",
                    user!.username !== message.from_user.username ? "" : "bg-gray-100"
                )}
            >
                <span className="block" style={{fontSize: "0.8rem",lineHeight: "1rem"}}>
                    {message.from_user.username}
                </span>
                <div className="flex items-end">

                    <span className="block">{message.content}</span>
                    <span
                        className="ml-2"
                        style={{
                            fontSize: "0.6rem",
                            lineHeight: "1rem"
                        }}
                    >
                        {formatMessageTimestamp(message.timestamp)}
                    </span>
                </div>
            </div>
        </li>
    );
}