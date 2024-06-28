import "./App.scss"
import { MantineProvider } from "@mantine/core"
import { SideNavbar, SidebarNavList } from "./components/sidebar/sidebar"
import { ConversationComp } from "./components/Conversation/conversation"
import { IconMessages } from "@tabler/icons-react"
import UserInfoModal from "./components/UserInfoModal/UserInfoModal"
import { useEffect } from "react"
import { getAllConversations } from "./redux/Conversation/conversationSlice"
import { useAppDispatch, useAppSelector } from "./redux/store"
import { userSelector } from "./redux/User/userSlice"

const navList: SidebarNavList = [{ icon: IconMessages, label: "Conversations" }]

function App() {
  const dispatch = useAppDispatch()
  const user = useAppSelector(userSelector)
  useEffect(() => {
    if (user.name) dispatch(getAllConversations(user))
  }, [user])
  return (
    <MantineProvider>
      <UserInfoModal />
      <div className="layout-wrapper">
        <SideNavbar navList={navList} />
        <div className="content">
          <ConversationComp />
        </div>
      </div>
    </MantineProvider>
  )
}

export default App
