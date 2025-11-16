import { create } from 'zustand'
import type { MessageInstance } from 'antd/es/message/interface'

interface MessageStore {
	messageApi: MessageInstance | null
	setMessageApi: (api: MessageInstance) => void
}

export const useMessageStore = create<MessageStore>(set => ({
	messageApi: null,
	setMessageApi: (api: MessageInstance) => set({ messageApi: api }),
}))
