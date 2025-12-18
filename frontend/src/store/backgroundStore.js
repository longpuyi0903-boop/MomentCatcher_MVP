import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

/**
 * 全局背景状态管理
 * 使用持久化存储，确保刷新后保持选择
 * 修复：使用 sessionChoiceMade（不持久化）来区分新登录和会话内切换
 */
export const useBackgroundStore = create(
  persist(
    (set, get) => ({
      // 每个用户的背景选择（key: user_id, value: imagePath）
      userBackgrounds: {},
      
      // 当前用户的背景图片路径（null表示未选择）
      // 这个会被持久化，用于 Memories 页显示背景
      selectedBackground: null,
      
      // 背景是否已加载完成（用于控制问候语显示时机）
      backgroundLoaded: false,
      
      // 粒子系统是否已初始化
      particlesInitialized: false,
      
      // 是否已经完成过背景选择流程（不持久化，用于区分新会话和会话内切换）
      // 这个不会被持久化，每次刷新页面都会重置为 false
      sessionChoiceMade: false,
      
      // 记录当前会话属于哪个用户（不持久化）
      // 用于区分"新登录"和"从Memories返回"：组件卸载重挂载时，如果sessionUserId还在，说明是同会话返回
      sessionUserId: null,
      
      // 设置当前用户ID并加载对应的背景
      setCurrentUserId: (userId) => {
        const state = get()
        const userBg = state.userBackgrounds[userId] || null
        
        // 恢复背景（用于 Memories 页显示）
        set({ 
          selectedBackground: userBg,
          backgroundLoaded: false,
          particlesInitialized: false,
          // 不清除 sessionChoiceMade，因为从 Memories 返回时应该保持 true
        })
      },
      
      // 设置选中的背景（关联到当前用户）
      setSelectedBackground: (imagePath, userId) => {
        const state = get()
        const newUserBackgrounds = { ...state.userBackgrounds }
        if (userId) {
          newUserBackgrounds[userId] = imagePath
        }
        set({ 
          userBackgrounds: newUserBackgrounds,
          selectedBackground: imagePath,
          sessionChoiceMade: true, // 标记本轮会话已选择过背景
          sessionUserId: userId, // 绑定当前会话用户ID
          backgroundLoaded: false, 
          particlesInitialized: false
        })
      },
      
      // 更新背景数据但不改变 sessionChoiceMade（用于名字更新时迁移数据）
      updateBackgroundData: (imagePath, userId) => {
        const state = get()
        const newUserBackgrounds = { ...state.userBackgrounds }
        if (userId) {
          newUserBackgrounds[userId] = imagePath
        }
        set({ 
          userBackgrounds: newUserBackgrounds,
          selectedBackground: imagePath,
          // 不改变 sessionChoiceMade，保持当前值
          // 不改变 sessionUserId，保持当前值
          backgroundLoaded: false, 
          particlesInitialized: false
        })
      },
      
      // 设置 sessionChoiceMade（用于新会话时重置）
      setSessionChoiceMade: (value) => {
        set({ sessionChoiceMade: value })
      },
      
      // 设置会话用户ID（用于新会话时绑定）
      setSessionUserId: (userId) => {
        set({ sessionUserId: userId })
      },
      
      // 标记背景已加载
      setBackgroundLoaded: (loaded) => {
        set({ backgroundLoaded: loaded })
      },
      
      // 标记粒子系统已初始化
      setParticlesInitialized: (initialized) => {
        set({ particlesInitialized: initialized })
      },
      
      // 检查是否需要显示背景选择器（基于当前用户）
      shouldShowCarousel: (userId) => {
        const state = get()
        if (!userId) return true // 没有用户ID，显示选择器
        // 如果当前用户没有选择过背景，显示选择器
        return !state.userBackgrounds[userId]
      },
      
      // 重置背景（用于测试）
      resetBackground: (userId) => {
        const state = get()
        const newUserBackgrounds = { ...state.userBackgrounds }
        if (userId) {
          delete newUserBackgrounds[userId]
        }
        set({ 
          userBackgrounds: newUserBackgrounds,
          selectedBackground: null, 
          backgroundLoaded: false, 
          particlesInitialized: false
        })
      }
    }),
    {
      name: 'moment-catcher-background', // localStorage key
      storage: createJSONStorage(() => localStorage),
      // 核心设置：只持久化这些字段，sessionChoiceMade 和 sessionUserId 不会被持久化
      partialize: (state) => ({
        selectedBackground: state.selectedBackground,
        userBackgrounds: state.userBackgrounds,
        // sessionChoiceMade 和 sessionUserId 不在这里，所以不会被持久化
      }),
    }
  )
)

