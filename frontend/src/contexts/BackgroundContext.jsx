import { createContext, useContext, useState, useEffect } from 'react'

const BackgroundContext = createContext(null)

export const BackgroundProvider = ({ children }) => {
  const [selectedBackground, setSelectedBackground] = useState(null)
  const [isBackgroundSelected, setIsBackgroundSelected] = useState(false)

  // 从 localStorage 恢复背景选择状态
  useEffect(() => {
    const saved = localStorage.getItem('momentCatcher_selectedBackground')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setSelectedBackground(parsed)
        setIsBackgroundSelected(true)
      } catch (e) {
        console.error('Failed to parse saved background:', e)
      }
    }
  }, [])

  // 保存背景选择到 localStorage
  const selectBackground = (background) => {
    setSelectedBackground(background)
    setIsBackgroundSelected(true)
    localStorage.setItem('momentCatcher_selectedBackground', JSON.stringify(background))
  }

  // 清除背景选择（用于测试或重置）
  const clearBackground = () => {
    setSelectedBackground(null)
    setIsBackgroundSelected(false)
    localStorage.removeItem('momentCatcher_selectedBackground')
  }

  return (
    <BackgroundContext.Provider
      value={{
        selectedBackground,
        isBackgroundSelected,
        selectBackground,
        clearBackground
      }}
    >
      {children}
    </BackgroundContext.Provider>
  )
}

export const useBackground = () => {
  const context = useContext(BackgroundContext)
  if (!context) {
    throw new Error('useBackground must be used within BackgroundProvider')
  }
  return context
}

