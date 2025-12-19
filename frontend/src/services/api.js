import axios from 'axios'

// 生产环境使用环境变量，开发环境使用相对路径（通过vite proxy）
// 如果设置了VITE_API_BASE_URL，使用它；否则使用相对路径（开发环境通过vite proxy转发）
let API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
// 确保URL包含协议（如果提供了域名但没有协议，自动添加https://）
if (API_BASE_URL && !API_BASE_URL.startsWith('http') && !API_BASE_URL.startsWith('/')) {
  API_BASE_URL = `https://${API_BASE_URL}`
} else if (API_BASE_URL && !API_BASE_URL.startsWith('http') && API_BASE_URL.includes('.railway.app')) {
  API_BASE_URL = `https://${API_BASE_URL}`
}
console.log('🔧 [API] 最终 baseURL:', API_BASE_URL)

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
  try {
    console.log('📡 [API] 请求 startMomentAPI, userId:', userId)
    console.log('📡 [API] baseURL:', API_BASE_URL)
    const response = await api.post('/moments/start', {
      user_id: userId,
    })
    console.log('📡 [API] 响应状态:', response.status)
    console.log('📡 [API] 响应headers:', response.headers)
    console.log('📡 [API] 响应数据类型:', typeof response.data)
    console.log('📡 [API] 响应数据原始值:', response.data)
    console.log('📡 [API] 响应数据JSON:', JSON.stringify(response.data, null, 2))
    console.log('📡 [API] greeting字段:', response.data?.greeting)
    console.log('📡 [API] moment_id字段:', response.data?.moment_id)
    return response.data
  } catch (error) {
    console.error('❌ [API] startMomentAPI 错误:', error)
    console.error('❌ [API] 错误响应:', error.response?.data)
    console.error('❌ [API] 错误状态:', error.response?.status)
    throw error
  }
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
  try {
    console.log('📡 [ASR API] 开始上传音频文件:', { name: audioFile.name, type: audioFile.type, size: audioFile.size })
    const formData = new FormData()
    formData.append('audio_file', audioFile)
    
    const response = await api.post('/asr', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    console.log('📡 [ASR API] 响应状态:', response.status)
    console.log('📡 [ASR API] 响应数据:', JSON.stringify(response.data, null, 2))
    console.log('📡 [ASR API] text字段:', response.data?.text)
    return response.data
  } catch (error) {
    console.error('❌ [ASR API] 错误:', error)
    console.error('❌ [ASR API] 错误响应:', error.response?.data)
    throw error
  }
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

