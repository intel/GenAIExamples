import { KeyboardEventHandler, SyntheticEvent, useEffect, useRef, useState } from "react"
import styleClasses from "./conversation.module.scss"
import { ActionIcon, Button, Text, Textarea, Title, rem } from "@mantine/core"
import { IconArrowRight, IconMessagePlus, IconTrash } from "@tabler/icons-react"
import { useAppSelector } from "../../redux/store"
import {
  conversationSelector,
  deleteConversationById,
  newConversation
} from "../../redux/Conversation/conversationSlice"
import { useAppDispatch } from "../../redux/store"
import { doConversation } from "../../redux/Conversation/conversationSlice"
import { userSelector } from "../../redux/User/userSlice"
import { ConversationContext } from "./conversationContext"
import { ConversationMessage } from "./conversationMessage"

const componentTitle = "Conversations"

const toSend = "Enter"

export function ConversationComp() {
  const { selectedConversation, selectedConversationId, onGoingPrompt, onGoingResult } =
    useAppSelector(conversationSelector)
  const user = useAppSelector(userSelector)
  const [prompt, setPrompt] = useState<string>("")
  const dispatch = useAppDispatch()

  const promptInputRef = useRef<HTMLTextAreaElement>(null)

  const scrollViewport = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollToBottom()
  }, [onGoingPrompt, onGoingResult, selectedConversation])

  const handleSubmit = () => {
    doConversation({
      user,
      prompt,
      temperature: 0.3,
      inferenceModel: "intel.neuralchat",
      tokenLimit: 500,
      conversationId: selectedConversationId
    })
    setPrompt("")
  }

  const scrollToBottom = () => {
    scrollViewport.current!.scrollTo({ top: scrollViewport.current!.scrollHeight })
  }

  const handleKeyDown: KeyboardEventHandler = (event) => {
    if (!event.shiftKey && event.key === toSend) {
      handleSubmit()
      setTimeout(() => {
        setPrompt("")
      }, 1)
    }
  }

  const handleDelete = () => {
    dispatch(deleteConversationById({ user, conversationId: selectedConversationId }))
  }

  const handleNwConversation = () => {
    dispatch(newConversation())
  }

  const handleChange = (event: SyntheticEvent) => {
    event.preventDefault()
    setPrompt((event.target as HTMLTextAreaElement).value)
  }

  const messages =
    selectedConversation?.messages?.map((curr) => (
      <>
        <ConversationMessage
          key={`${curr.message_id}_human`}
          date={curr.created_at * 1000}
          human={true}
          message={curr.human}
        />
        <ConversationMessage
          key={`${curr.message_id}_ai`}
          date={curr.created_at * 1000}
          human={false}
          message={curr.assistant}
        />
      </>
    )) ?? []

  return (
    <div className={styleClasses.conversationWrapper}>
      <ConversationContext title={componentTitle} />

      <div className={styleClasses.conversationContent}>
        {selectedConversation && (
          <div className={styleClasses.conversationContentMessages}>
            <div className={styleClasses.conversationTitle}>
              <Title order={3}> {selectedConversation.first_query} </Title>

              <span className={styleClasses.spacer}></span>

              {selectedConversationId && (
                <>
                  <ActionIcon onClick={handleNwConversation} size={32} variant="default">
                    <IconMessagePlus />
                  </ActionIcon>
                  <ActionIcon onClick={handleDelete} size={32} variant="default">
                    <IconTrash />
                  </ActionIcon>
                </>
              )}
            </div>

            <div className={styleClasses.historyContainer} ref={scrollViewport}>
              {selectedConversation.message_count <= 0 && !onGoingPrompt && (
                <>
                  <div className="emptyMessage">Wow. Such emptiness.</div>
                  <div className="infoMessage">Start by asking a question</div>
                </>
              )}

              {selectedConversation.message_count > 0 && messages}
              {onGoingPrompt && (
                <ConversationMessage key={`_human`} date={Date.now()} human={true} message={onGoingPrompt} />
              )}
              {onGoingResult && (
                <ConversationMessage key={`_ai`} date={Date.now()} human={false} message={onGoingResult} />
              )}
            </div>

            <div className={styleClasses.conversationActions}>
              <Textarea
                radius="xl"
                size="md"
                placeholder="Ask a question"
                ref={promptInputRef}
                onKeyDown={handleKeyDown}
                onChange={handleChange}
                value={prompt}
                rightSectionWidth={42}
                rightSection={
                  <ActionIcon onClick={handleSubmit} size={32} radius="xl" variant="filled">
                    <IconArrowRight style={{ width: rem(18), height: rem(18) }} stroke={1.5} />
                  </ActionIcon>
                }
              // {...props}
              />
            </div>
          </div>
        )}

        {!selectedConversation && (
          <div className={styleClasses.conversationSplash}>
            <Text size="lg" c="dimmed">
              Select a conversation
            </Text>

            <Text size="md">or</Text>

            <Button>Start New Conversation</Button>
          </div>
        )}
      </div>
    </div>
  )
}
