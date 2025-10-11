import { useState, useEffect } from 'preact/hooks';

import "./CassiaNotify.css";

export type CassiaNotifyType = "info" | "success" | "error" | "warning";

export const CassiaNotifyTypes = {
    INFO: "info",
    SUCCESS: "success",
    ERROR: "error",
    WARNING: "warning",
} as const;

export interface CassiaNotifyProps {
    message: string;
    title?: string;
    type?: CassiaNotifyType;
    duration?: number; // 毫秒
    onClose?: () => void;
}

export function CassiaNotify({ message, title, type = "info", duration = 5000, onClose }: CassiaNotifyProps) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        if (duration > 0) {
            const timer = setTimeout(() => {
                setVisible(false);
                onClose?.();
            }, duration);
            return () => clearTimeout(timer);
        }
    }, [duration]);

    if (!visible) return null;

    return (
        <div class={`cassia-notify cassia-notify-${type}`}>
            {
                title && (
                    <div class="cassia-notify-title">
                        {title}
                    </div>
                )
            }
            <span>{message}</span>
            <button class="cassia-notify-close" onClick={() => { setVisible(false) }}>x</button>
        </div>
    );
}