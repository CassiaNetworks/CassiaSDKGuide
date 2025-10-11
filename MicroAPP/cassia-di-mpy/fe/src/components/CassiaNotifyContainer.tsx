import { useImperativeHandle, useState } from "preact/hooks";
import { CassiaNotify, CassiaNotifyProps } from "./CassiaNotify";
import { forwardRef } from "preact/compat";

export interface CassiaNotifyContainerRef {
    addNotify: (notify: CassiaNotifyProps) => void;
}

export const CassiaNotifyContainer = forwardRef<CassiaNotifyContainerRef>((_props, ref) => {
    const [notifies, setNotifies] = useState<CassiaNotifyProps[]>([]);

    const addNotify = (notify: CassiaNotifyProps) => {
        setNotifies(prev => [...prev, notify]);
    };

    const removeNotify = (index: number) => {
        setNotifies(prev => prev.filter((_, i) => i !== index));
    };

    useImperativeHandle(ref, () => ({
        addNotify,
    }));

    return (
        <div class="cassia-notify-container">
            {
                notifies.map((n, i) => (
                    <CassiaNotify
                        key={i}
                        {...n}
                        onClose={() => removeNotify(i)}
                    />
                ))
            }
            {null as any as { addNotify: typeof addNotify }}
        </div>
    );
});

