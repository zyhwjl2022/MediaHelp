import { requestClient } from '#/api/request';

/**
 * 获取系统配置
 */
export async function getSysConfigApi(params: any) {
  return requestClient.get('/sysSetting/config', { params });
}

/**
 * 更新系统配置
 */
export async function updateSysConfigApi(data: any) {
  return requestClient.put('/sysSetting/config', data);
}

/**
 * 获取企业微信机器人通知配置
 */
export async function getNoticeConfigApi(params: any) {
  return requestClient.get('/notify/config', { params });
}

/**
 * 更新企业微信机器人通知配置
 */
export async function updateNoticeConfigApi(data: any) {
  return requestClient.put('/notify/config', data);
}

/**
 * 发送测试消息
 */
export async function sendNoticeMessageApi(data: any) {
  return requestClient.post('/notify/send', data);
}

/**
 * 获取资源频道设置
 */
export async function getResourceChannelConfigApi(params: any) {
  return requestClient.get('/sysSetting/tg-resource/config', { params });
}

/**
 * 更新资源频道设置
 */
export async function updateResourceChannelConfigApi(data: any) {
  return requestClient.put('/sysSetting/tg-resource/config', data);
}
