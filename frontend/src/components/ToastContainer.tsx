import type { Toast } from '../hooks/useToast';
import { X } from 'lucide-react';

interface Props {
    toasts: Toast[];
    onRemove: (id: number) => void;
}

export default function ToastContainer({ toasts, onRemove }: Props) {
    if (toasts.length === 0) return null;
    return (
        <div className="toast-container fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
            {toasts.map((t) => (
                <div key={t.id} className={`toast toast-${t.type} pointer-events-auto flex items-center gap-3`}>
                    <span className="flex-1 text-[13px] font-medium text-gray-800 dark:text-gray-200">{t.message}</span>
                    <button onClick={() => onRemove(t.id)} className="p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors shrink-0">
                        <X size={14} />
                    </button>
                </div>
            ))}
        </div>
    );
}
