import { useState } from "react"
import { Tooltip, UnstyledButton, Stack, rem } from "@mantine/core"
import { IconHome2, IconLogout } from "@tabler/icons-react"
import classes from "./sidebar.module.scss"
import OpeaLogo from "../../assets/opea-icon-black.svg"
import { useAppDispatch } from "../../redux/store"
import { removeUser } from "../../redux/User/userSlice"

interface NavbarLinkProps {
  icon: typeof IconHome2
  label: string
  active?: boolean
  onClick?(): void
}

function NavbarLink({ icon: Icon, label, active, onClick }: NavbarLinkProps) {
  return (
    <Tooltip label={label} position="right" transitionProps={{ duration: 0 }}>
      <UnstyledButton onClick={onClick} className={classes.link} data-active={active || undefined}>
        <Icon style={{ width: rem(20), height: rem(20) }} stroke={1.5} />
      </UnstyledButton>
    </Tooltip>
  )
}

export interface SidebarNavItem {
  icon: typeof IconHome2
  label: string
}

export type SidebarNavList = SidebarNavItem[]

export interface SideNavbarProps {
  navList: SidebarNavList
}

export function SideNavbar({ navList }: SideNavbarProps) {
  const dispatch =useAppDispatch()
  const [active, setActive] = useState(0)

  const links = navList.map((link, index) => (
    <NavbarLink {...link} key={link.label} active={index === active} onClick={() => setActive(index)} />
  ))

  return (
    <nav className={classes.navbar}>
      <div className={classes.navbarLogo}>
        {/* <IconMathIntegralX /> */}
        <img className={classes.logoImg} src={OpeaLogo} alt="opea logo" />
      </div>

      <div className={classes.navbarMain}>
        <Stack justify="center" gap={0}>
          {links}
        </Stack>
      </div>
      <Stack justify="center" gap={0}>
        <NavbarLink icon={IconLogout} label="Logout" onClick={() => dispatch(removeUser())} />
      </Stack>
    </nav>
  )
}
