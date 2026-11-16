import { createContext, useContext } from 'react'

export type Tone = 'ok' | 'info' | 'error'

export const ToastContext = createContext<(text: string, tone?: Tone) => void>(() => {})

/** toast('Copied') shows a short confirmation at the bottom of the screen. */
export const useToast = () => useContext(ToastContext)
