import React from "react";



export function MainLayout({children}: {children: React.ReactNode}) {
    return (
        <>
            <header>
                {/* Nav Component */}
            </header>
            <main>
                {children}
            </main>
            <footer>
                {/* Footer Component */}
            </footer>
        </>
    )
}