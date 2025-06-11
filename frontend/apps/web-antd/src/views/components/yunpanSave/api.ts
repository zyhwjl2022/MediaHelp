import { requestClient } from '#/api/request';

/**
 * quark 分享文件列表
 */
export const getQuarkShareFileListApi = (params: any) => {
  return requestClient.get('/quark/share/files', { params });
};
