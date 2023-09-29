import { useFormik } from "formik";
import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../contexts/AuthContext";

export function Login() {
    const navigate = useNavigate();
    const [error, setError] = useState<any | null>(null);
    const { user, login } = useContext(AuthContext);

    const formik = useFormik({
        initialValues: {
            username: "",
            password: ""
        },
        onSubmit: async (values, { setSubmitting }) => {
            setSubmitting(true);
            const { username, password } = values;
            const res = await login(username, password);
            if (res.data) {
                if (res.data) {
                    setError(res.data);
                }
            } else {
                navigate("/");
            }
            setSubmitting(false);
        }
    });

    useEffect(() => {
        if (user) {
            navigate("/");
        }
    }, [user]);

    return (
        <div>
            <div className="flex min-h-full flex-col justify-center px-6 py-12 lg:px-8">
                <div className="sm:mx-auto sm:w-full sm:max-w-sm">
                    <h1 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900">Sign in to your account</h1>
                </div>
                <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
                    <form className="space-y-6" onSubmit={formik.handleSubmit}>
                        <div>
                            {error?.non_field_errors && <div className="text-red-600">{error?.non_field_errors}</div>}
                            <label className="block text-sm font-medium leading-6 text-gray-900">
                                Login:
                            </label>
                            {error?.username && <div className="text-red-600">{error?.username}</div>}
                            <div className="mt-2">
                                <input
                                    value={formik.values.username}
                                    onChange={formik.handleChange}
                                    type="text"
                                    name="username"
                                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                />
                            </div>
                        </div>
                        <div >
                            <label className="block text-sm font-medium leading-6 text-gray-900">
                                Password
                            </label>
                            {error?.password && <div className="text-red-600">{error?.password}</div>}
                            <div className="mt-2">
                                <input
                                    value={formik.values.password}
                                    onChange={formik.handleChange}
                                    type="password"
                                    name="password"
                                    className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                />
                            </div>
                        </div>
                        <button
                            type="submit"
                            className="flex w-full justify-center rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            {formik.isSubmitting ? "Signing in..." : "Sign in"}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}