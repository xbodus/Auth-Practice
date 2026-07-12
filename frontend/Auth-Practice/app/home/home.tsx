import { useState } from "react";


export function Index() {
    const [data, setData] = useState<{message: string | null}>({message: null});

    const handleSubmit = () => {
        fetch("http://localhost:8000", {
            credentials: "include"
        })
            .then(r => r.json())
            .then(d => setData(d))
            .catch(error => console.log("Failed to connect to API"))
    }

    return (
        <>
            <h1>Hello World!</h1>
            <button onClick={() => handleSubmit()}>Check API Connection</button>
            {data.message && <div>{data.message}</div>}
        </>
    )
}