import { useContext, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AuthContext } from "../contexts/AuthContext";

interface UserResponse {
    username: string;
    name: string;
    url: string;
}

export function Conversations() {
    const { user } = useContext(AuthContext);
    const [users, setUsers] = useState<UserResponse[]>([]);

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

    function createConversationName(username: string) {
        const namesAlph = [user?.username, username].sort();
        return `${namesAlph[0]}__${namesAlph[1]}`;
    }

    return (
        <div>
            <div className="px-4 sm:px-0">
                <h3 className="text-base font-semibold leading-7 text-gray-900">User list:</h3>
            </div>
            <div className="mt-6">
                {users
                    .filter((u) => u.username !== user?.username)
                    .map((u) => (
                        <div className="mt-0 border-t border-gray-100" key={u.username + 2}>
                        <Link
                            key={u.username}
                            to={`chats/${createConversationName(u.username)}`}
                        >
                            <div className=" px-2 py-2 text-sm font-medium leading-6 text-gray-900">{u.username}</div>
                        </Link>
                        </div>
                    ))}
            </div>
        </div>
    );
}