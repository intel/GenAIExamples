import { IconAi, IconUser } from "@tabler/icons-react"
import style from "./conversationMessage.module.scss"
import { Group, Text } from "@mantine/core"
import { DateTime } from "luxon"

export interface ConversationMessageProps {
  message: string
  human: boolean
  date: number
}

export function ConversationMessage({ human, message, date }: ConversationMessageProps) {
  const dateFormat = () => {
    // console.log(date)
    // console.log(new Date(date))
    return DateTime.fromJSDate(new Date(date)).toLocaleString(DateTime.DATETIME_MED)
  }

  return (
    <div className={style.conversationMessage}>
      <Group>
        {/* <Avatar
          src="https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/avatars/avatar-1.png"
          alt="Jacob Warnhalter"
          radius="xl"
        /> */}

        {human && <IconUser />}
        {!human && <IconAi />}

        <div>
          <Text size="sm">
            {human && "User"} {!human && "Assistant"}
          </Text>
          <Text size="xs" c="dimmed">
            {dateFormat()}
          </Text>
        </div>
      </Group>
      <Text pl={54} pt="sm" size="sm">
        {message}
      </Text>

      {/* <div className={style.header}>
        {human && <IconUser />}
        {!human && <IconAi />}
      </div>

      <div className={style.message}>{message}</div> */}
    </div>
  )
}
