import { ScrollAreaAutosize, Title } from "@mantine/core"

import contextStyles from "../../styles/components/context.module.scss"
import { useAppDispatch, useAppSelector } from "../../redux/store"
import {
  conversationSelector,
  getConversationById,
  setSelectedConversationId
} from "../../redux/Conversation/conversationSlice"
import { userSelector } from "../../redux/User/userSlice"

export interface ConversationContextProps {
  title: string
}

export function ConversationContext({ title }: ConversationContextProps) {
  const { selectedConversationId, conversations } = useAppSelector(conversationSelector)
  const user = useAppSelector(userSelector)
  const dispatch = useAppDispatch()

  const converstaionList = conversations?.map((curr) => (
    <div
      className={contextStyles.contextListItem}
      data-active={selectedConversationId === curr.conversation_id || undefined}
      onClick={(event) => {
        event.preventDefault()
        dispatch(setSelectedConversationId(curr.conversation_id))
        dispatch(getConversationById({ user, conversationId: curr.conversation_id }))
      }}
      key={curr.conversation_id}
    >
      <div className={contextStyles.contextItemName} title={curr.first_query}>{curr.first_query}</div>
    </div>
  ))

  return (
    <div className={contextStyles.contextWrapper}>
      <Title order={3} className={contextStyles.contextTitle}>
        {title}
      </Title>
      <ScrollAreaAutosize type="hover" scrollHideDelay={0}>
        <div className={contextStyles.contextList}>{converstaionList}</div>
      </ScrollAreaAutosize>
    </div>
  )
}
