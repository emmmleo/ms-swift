import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000
})

export const login = (username, password) => {
  return api.post('/login', { username, password })
}

export const getTasks = (group) => {
  return api.get('/tasks', { params: { group } })
}

export const launchTraining = (data) => {
  return api.post('/launch', data)
}

export const getLog = (logFile, offset) => {
  return api.get('/log', { params: { log_file: logFile, offset } })
}

export const killTask = (pid, outputDir) => {
  return api.post('/kill', { pid, output_dir: outputDir })
}
