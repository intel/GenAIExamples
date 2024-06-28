import { SyntheticEvent, useEffect, useState } from 'react'
import { useDisclosure } from '@mantine/hooks';
import { TextInput, Button, Modal } from '@mantine/core';
import { useDispatch, useSelector } from 'react-redux';
import { userSelector, setUser } from '../../redux/User/userSlice';


const UserInfoModal = () => {
    const [opened, { open, close }] = useDisclosure(false);
    const { name } = useSelector(userSelector);
    const [username, setUsername] = useState(name || "");
    const dispatch = useDispatch();
    const handleSubmit = (event: SyntheticEvent) => {
        event.preventDefault()
        if(username){
            close();
            dispatch(setUser(username));
            setUsername("")
        }
        
    }
    useEffect(() => {
        if (!name) {
            open();
        }
    }, [name])
    return (
        <>
            <Modal opened={opened} onClose={close} title="Tell us who you are ?" centered>
                <>
                    <form onSubmit={handleSubmit} >
                        <TextInput label="Username" placeholder="Username" onChange={(event)=> setUsername(event?.currentTarget.value)} value={username} data-autofocus />
                        <Button fullWidth onClick={handleSubmit} mt="md">
                            Submit
                        </Button>
                    </form>
                    
                </>
            </Modal>
        </>

    )
}

export default UserInfoModal