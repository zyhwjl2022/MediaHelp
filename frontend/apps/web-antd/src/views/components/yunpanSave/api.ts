import { requestClient } from '#/api/request';

/**
 * quark 分享文件列表
 */
export const getQuarkShareFileListApi = (params: any) => {
  return requestClient.get('/quark/share/files', { params });
};

/**
 * quark 保存文件
 */
export const saveQuarkFileApi = (data: any) => {
  return requestClient.post('/quark/share/save', data);
};

/**
 * quark 获取文件列表
 */
export const getQuarkFileListApi = (params: any) => {
  return requestClient.get('/quark/files', { params });
};

/**
 * quark 获取文件夹目录对应的fid
 */
export const getQuarkFidsApi = (data: any) => {
  return requestClient.post('/quark/fids', data);
};

/**
 * quark 重命名文件
 */
export const renameQuarkFileApi = (data: any) => {
  return requestClient.post('/quark/rename', data);
};

/**
 * 获取目录列表
 */
export const postQuarkCreateDirectoryApi = (data: any) => {
  return requestClient.post('/quark/directory', data);
};

/**
 * 删除文件
 */
export const deleteQuarkFileApi = (data: any) => {
  return requestClient.delete('/quark/files', { data });
};

/**
 * 189 获取文件列表
 */
export const getCloud189FileListApi = (data: any) => {
  return requestClient.post('/cloud189/files', data);
};

/**
 * 189 获取分享文件列表
 */
export const getCloud189ShareFileListApi = (data: any) => {
  return requestClient.post('/cloud189/share/files', data);
};

/**
 * 189 保存文件
 */
export const saveCloud189FileApi = (data: any) => {
  return requestClient.post('/cloud189/share/save', data);
};

/**
 * 189 重命名文件
 */
export const createCloud189FolderApi = (data: any) => {
  return requestClient.post('/cloud189/folder', data);
};

/**
 * 189 重命名文件
 */
export const renameCloud189FileApi = (data: any) => {
  return requestClient.post('/cloud189/rename', data);
};

/**
 * 189 删除文件
 */
export const deleteCloud189FileApi = (data: any) => {
  return requestClient.post('/cloud189/delete', data);
};
