import { useRef, useState } from "preact/hooks";

import "./CassiaTooltip.css";

interface CassiaTooltipProps {
    children?: preact.ComponentChildren;
}

export function CassiaTooltip({ children }: CassiaTooltipProps) {
    const [visible, setVisible] = useState(false);
    const timeoutRef = useRef<number | null>(null);

    const handleMouseEnter = () => {
        clearTimeoutRef();
        setVisible(true);
    };

    const handleMouseLeave = () => {
        clearTimeoutRef();
        setTimeoutRef();
    };


    const clearTimeoutRef = () => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
            timeoutRef.current = null;
        }
    };

    const setTimeoutRef = () => {
        clearTimeoutRef();
        timeoutRef.current = window.setTimeout(() => {
            setVisible(false);
            timeoutRef.current = null;
        }, 50);
    };

    return (
        <div
            class="cassia-tooltip-container"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <span class="cassia-tooltip-marker"
            >?</span>

            <div class="cassia-tooltip-content" onMouseEnter={handleMouseEnter}
                style={{ opacity: visible ? "1" : "0" }}>
                {children}
            </div>
        </div>
    );
}