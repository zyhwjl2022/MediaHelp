import { requestClient } from '#/api/request';

/**
 * 获取系统配置
 */
export async function getSysConfigApi(params: any) {
  return requestClient.get('/sysSetting/config', { params });
}
