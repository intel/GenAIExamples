import { Title } from "@mantine/core"
import classes from "./context.module.scss"
import { ConversationList } from "../redux/Conversation/conversation"
import { useAppDispatch, useAppSelector } from "../redux/store"
import { userSelector } from "../redux/User/userSlice"
import { conversationSelector, getConversationById, setSelectedConversationId } from "../redux/Conversation/conversationSlice"

export interface ContextListItem {
  displayName: string
}

export interface ContextBarProps {
  label: string
  data: ConversationList
}

export function ContextBar() {
  // const [active] = useState(label)
  // const [activeLink, setActiveLink] = useState<string | null>(null)
  const { selectedConversationId, conversations } = useAppSelector(conversationSelector)
  const user = useAppSelector(userSelector);
  const dispatch = useAppDispatch();

  const links = conversations.map((conversation) => (
    <a
      className={classes.link}
      data-active={selectedConversationId === conversation.conversation_id || undefined}
      href="#"
      onClick={(event) => {
        event.preventDefault()
        dispatch(setSelectedConversationId(conversation.conversation_id))
        dispatch(getConversationById({user,conversationId:conversation.conversation_id}))
      }}
      key={conversation.conversation_id}
    >
      {conversation.first_query}
    </a>
  ))

  return (
    <div className={classes.main}>
      <Title order={4} className={classes.title}>
        {"conversations"}
      </Title>

      {links}
    </div>
  )
}
