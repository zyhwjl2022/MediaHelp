export const getTaskByUrl = (url: string) => {
  if (url.includes('quark')) {
    return 'quark_auto_save';
  } else if (url.includes('cloud.189')) {
    return 'cloud189_auto_save';
  }
  return '';
};

export const getCloudTypeByUrl = (url: string) => {
  if (url.includes('quark')) {
    return 'quark';
  } else if (url.includes('cloud.189')) {
    return 'tianyiyun';
  }
  return '';
};

export const getCloudTypeByTask = (task: string) => {
  if (task === 'quark_auto_save') {
    return 'quark';
  } else if (task === 'cloud189_auto_save') {
    return 'tianyiyun';
  }
  return '';
};
