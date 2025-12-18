import axios from 'axios'

// 生产环境使用环境变量，开发环境使用相对路径（通过vite proxy）
// 如果设置了VITE_API_BASE_URL，使用它；否则使用相对路径（开发环境通过vite proxy转发）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 用于构建音频URL的完整地址（如果API_BASE_URL是相对路径，需要单独处理）
export const getAudioBaseURL = () => {
  if (API_BASE_URL.startsWith('http')) {
    return API_BASE_URL.replace('/api', '')
  }
  // 开发环境
  return 'http://localhost:8000'
}

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 初始化连接
export const initAPI = async (userName, agentName) => {
  const response = await api.post('/init', {
    user_name: userName,
    agent_name: agentName,
  })
  return response.data
}

// 开始新 Moment
export const startMomentAPI = async (userId) => {
  const response = await api.post('/moments/start', {
    user_id: userId,
  })
  return response.data
}

// 发送消息
export const chatAPI = async (userId, message, history = []) => {
  const response = await api.post('/chat', {
    user_id: userId,
    message: message,
    history: history.map(msg => ({
      role: msg.role,
      content: msg.content,
    })),
  })
  return response.data
}

// 保存 Moment
export const saveMomentAPI = async (userId) => {
  const response = await api.post('/moments/save', {
    user_id: userId,
  })
  return response.data
}

// 获取所有 Moments
export const getMomentsAPI = async (userId) => {
  const response = await api.get('/moments', {
    params: { user_id: userId },
  })
  return response.data
}

// 获取风格画像
export const getStyleProfileAPI = async (userId) => {
  const response = await api.get('/style/profile', {
    params: { user_id: userId },
  })
  return response.data
}

// 文本转语音
export const ttsAPI = async (text) => {
  const response = await api.post('/tts', { text }, {
    responseType: 'blob', // 接收音频文件
  })
  // 创建音频 URL
  const audioUrl = URL.createObjectURL(response.data)
  return audioUrl
}

// 语音转文字（ASR）
export const asrAPI = async (audioFile) => {
  const formData = new FormData()
  formData.append('audio_file', audioFile)
  
  const response = await api.post('/asr', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// 更新用户名字
export const updateNamesAPI = async (oldUserId, newUserName, newAgentName) => {
  const response = await api.post('/update-names', {
    old_user_id: oldUserId,
    new_user_name: newUserName,
    new_agent_name: newAgentName,
  })
  return response.data
}

