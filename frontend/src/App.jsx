import { useState } from 'react'
import LandingPage from './components/LandingPage'
import MainInterface from './components/MainInterface'
import './App.css'

function App() {
  const [userInfo, setUserInfo] = useState(null)

  const handleInit = (userName, agentName) => {
    setUserInfo({
      user_id: `${userName}_${agentName}`,
      user_name: userName,
      agent_name: agentName
    })
  }

  if (!userInfo) {
    return <LandingPage onInit={handleInit} />
  }

  const handleUserInfoUpdate = (updatedUserInfo) => {
    if (updatedUserInfo) {
      // 更新名字
      setUserInfo(updatedUserInfo)
    } else {
      // 重置（清空所有数据）
      setUserInfo(null)
    }
  }

  return <MainInterface userInfo={userInfo} onUserInfoUpdate={handleUserInfoUpdate} />
}

export default App


