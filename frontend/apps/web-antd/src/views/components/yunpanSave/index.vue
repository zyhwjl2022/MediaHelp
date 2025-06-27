<script setup lang="ts">
import type { PropType } from 'vue';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

import { Button, message, Modal } from 'ant-design-vue';

import FolderSelect from '../FolderSelect/index.vue';
import {
  createCloud189FolderApi,
  deleteCloud189FileApi,
  deleteQuarkFileApi,
  getCloud189FileListApi,
  getCloud189ShareFileListApi,
  getQuarkFileListApi,
  getQuarkShareFileListApi,
  postQuarkCreateDirectoryApi,
  renameCloud189FileApi,
  renameQuarkFileApi,
  saveCloud189FileApi,
  saveQuarkFileApi,
} from './api';

const props = defineProps({
  item: {
    type: Object as PropType<any>,
    default: () => ({}),
  },
});

// 计算属性：获取分享链接
const shareUrl = computed(() => {
  return props.item?.cloudLinks?.[0] || '';
});

// 响应式数据定义
const fileList = ref<any[]>([]);
const selectedFile = ref<any[]>([]);
const stoken = ref<string>('');
const paths = ref<any[]>([]);
const fileList2 = ref<any[]>([]);
const paths2 = ref<any[]>([]);
const open = defineModel<boolean>('open', {
  default: false,
  type: Boolean,
});
const loading = defineModel<boolean>('loading', {
  default: false,
  type: Boolean,
});
const saveOperation = ['分享文件', '保存到'];
const currentStep = ref<number>(0);
const okText = computed(() => {
  return currentStep.value === 0 ? '保存到' : '保存';
});
const modalTitle = computed(() => {
  return saveOperation[currentStep.value];
});

const width = ref('800px');

// 窗口尺寸适配
const updateWidth = () => {
  const w = window.innerWidth;
  if (w < 640) {
    width.value = '90vw';
  } else if (w < 768) {
    width.value = '800px';
  } else if (w < 1024) {
    width.value = '1000px';
  } else if (w < 1280) {
    width.value = '1000px';
  } else {
    width.value = '1000px';
  }
};

// 生命周期钩子
onMounted(() => {
  updateWidth();
  window.addEventListener('resize', updateWidth);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
});

let lastShareUrl: any;

// 格式化夸克分享链接
const formatQuarkShareUrl = (dir: any = {}) => {
  const url = lastShareUrl ?? shareUrl.value;
  if (Object.keys(dir).length === 0 || dir.fid === 0) {
    lastShareUrl = url.match(/.*s\/[a-z0-9]+(\?pwd=[^#]+)?/)?.[0] || '';
    return lastShareUrl;
  } else if (url.includes(dir.fid)) {
    lastShareUrl = url.match(new RegExp(`.*/${dir.fid}[^/]*`))?.[0] || '';
    return lastShareUrl;
  } else if (url.includes('#/list/share')) {
    lastShareUrl = `${url}/${dir.fid}-${dir.name?.replace(/-/g, '*101')}`;
    return lastShareUrl;
  } else {
    lastShareUrl = `${url}#/list/share/${dir.fid}-${dir.name?.replace(/-/g, '*101')}`;
    return lastShareUrl;
  }
};

let filePaths: any[] = [];

// 优化：避免直接修改数组，返回新数组
const selfSavePaths = (dir: any, filePaths: any[]) => {
  if (dir.fid) {
    const index = filePaths.findIndex((item) => item.fid === dir.fid);
    return index === -1 ? [...filePaths, dir] : filePaths.slice(0, index + 1);
  } else {
    return [];
  }
};

// 定义响应式filepaths2
const filepaths2 = ref<any[]>([]);

// 获取分享文件列表
const getShareFileList = async (dir: any = {}) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    const res = await getQuarkShareFileListApi({
      share_url: formatQuarkShareUrl(dir),
    }).finally(() => {
      loading.value = false;
    });
    fileList.value = res.list ?? [];
    paths.value = res.paths ?? [];
    stoken.value = res?.share_info?.token ?? '';
  } else if (props.item?.cloudType === 'tianyiyun') {
    loading.value = true;
    const res = await getCloud189ShareFileListApi({
      share_url: shareUrl.value,
      file_id: dir.fid,
    }).finally(() => {
      loading.value = false;
    });
    const { fileListAO } = res;
    fileList.value = [
      ...(fileListAO?.folderList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        dir: true,
      })),
      ...(fileListAO?.fileList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        file: true,
      })),
    ];
    filePaths = selfSavePaths(dir, filePaths);
    paths.value = [...filePaths];
  }
};

// 获取目标文件列表
const getFileList = async (dir: any = {}) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    const res = await getQuarkFileListApi({ dir_id: dir.fid }).finally(() => {
      loading.value = false;
    });
    fileList2.value = res.list ?? [];
    filepaths2.value = selfSavePaths(dir, filepaths2.value); // 使用响应式filepaths2
    paths2.value = [...filepaths2.value];
  } else if (props.item?.cloudType === 'tianyiyun') {
    loading.value = true;
    const res = await getCloud189FileListApi({
      folder_id: dir.fid === undefined ? '-11' : String(dir.fid),
    }).finally(() => {
      loading.value = false;
    });
    const { fileListAO } = res;
    fileList2.value = [
      ...(fileListAO?.folderList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        dir: true,
      })),
      ...(fileListAO?.fileList ?? []).map((item: any) => ({
        ...item,
        file_name: item.name,
        fid: item.id,
        file: true,
      })),
    ];
    filePaths = selfSavePaths(dir, filePaths);
    filepaths2.value = filePaths; // 同步到filepaths2
    paths2.value = [...filepaths2.value];
  }
};

// 保存分享文件
const saveShareFile = async () => {
  if (props.item?.cloudType === 'quark') {
    const file_ids = selectedFile.value.map((item) => item.fid);
    const file_tokens = selectedFile.value.map((item) => item.share_fid_token);
    const target_dir = paths2.value[paths2.value.length - 1]?.fid ?? '0';
    // const pdir_fid = paths.value[paths.value.length - 1]?.fid ?? '0';
    // 优化：如果paths.value为空，则使用fileList的第一个文件夹ID
    const pdir_fid = paths?.value?.length > 0 
  ? paths.value[paths.value.length - 1]?.fid ?? fileList?.value?.[0]?.fid ?? '0' 
  : fileList?.value?.[0]?.fid ?? '0'; 
    return await saveQuarkFileApi({
      share_url: shareUrl.value,
      file_ids,
      file_tokens,
      target_dir,
      pdir_fid,
      stoken: stoken.value,
      keyword: props.item.keyword,
    });
  } else if (props.item?.cloudType === 'tianyiyun') {
    const target_folder_id =
      paths2.value[paths2.value.length - 1]?.fid ?? '-11';
    const file_ids =
      selectedFile.value.length > 0
        ? selectedFile.value.map((item) => ({
            fileId: item.fid,
            fileName: item.file_name,
            isFolder: item.dir,
          }))
        : fileList.value.map((item) => ({
            fileId: item.fid,
            fileName: item.file_name,
            isFolder: item.dir,
          }));
    return await saveCloud189FileApi({
      share_url: shareUrl.value,
      target_folder_id,
      file_ids,
    });
  }
};

// 监听open状态变化，重置所有状态
watch(open, (value) => {
  if (value) {
    lastShareUrl = undefined;
    fileList.value = [];
    fileList2.value = [];
    paths.value = [];
    paths2.value = [];
    filepaths2.value = []; // 关键：重置响应式filepaths2
    filePaths = [];
    selectedFile.value = [];
    currentStep.value = 0;
    getShareFileList();
  }
});

// 导航到指定目录
const navigateTo = (dir: any) => {
  if (currentStep.value === 0) {
    getShareFileList(dir);
  } else {
    getFileList(dir);
  }
};

// 确认操作
const onOk = async () => {
  if (currentStep.value === 0) {
    // 下一步
    currentStep.value = 1;
    if (fileList2.value.length === 0) {
      getFileList();
    }
  } else {
    // 保存
    await saveShareFile();
    open.value = false;
    message.success('保存成功');
  }
};

// 返回上一步
const onBack = () => {
  currentStep.value = 0;
};

// 创建文件夹
const createDir = async (fileName: any) => {
  if (!fileName) {
    message.error('请输入文件夹名称');
    return;
  }
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    await postQuarkCreateDirectoryApi({
      name: fileName,
      parent_id: paths2.value[paths2.value.length - 1]?.fid ?? '0',
    })
      .finally(() => {
        loading.value = false;
      })
      .then(() => {
        setTimeout(() => {
          getFileList({
            fid: paths2.value[paths2.value.length - 1]?.fid ?? '0',
          });
        }, 500);
      });
  } else if (props.item?.cloudType === 'tianyiyun') {
    loading.value = true;
    await createCloud189FolderApi({
      folder_name: fileName,
      parent_id: paths2.value[paths2.value.length - 1]?.fid ?? '-11',
    })
      .finally(() => {
        loading.value = false;
      })
      .then(() => {
        getFileList({
          fid: paths2.value[paths2.value.length - 1]?.fid ?? '-11',
        });
      });
  }
};

// 重命名文件/文件夹
const rename = async (_file: any) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    await renameQuarkFileApi({
      file_id: _file.fid,
      new_name: _file.file_name,
    })
      .finally(() => {
        loading.value = false;
      })
      .then(() => {
        getFileList({
          fid: paths2.value[paths2.value.length - 1]?.fid ?? '0',
        });
      });
  } else if (props.item?.cloudType === 'tianyiyun') {
    loading.value = true;
    await renameCloud189FileApi({
      file_id: _file.fid,
      new_name: _file.file_name,
    })
      .finally(() => {
        loading.value = false;
      })
      .then(() => {
        getFileList({
          fid: paths2.value[paths2.value.length - 1]?.fid ?? '-11',
        });
      });
  }
};

// 删除文件/文件夹
const deleteFile = async (_file: any) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    await deleteQuarkFileApi({
      file_ids: [_file.fid],
    })
      .finally(() => {
        loading.value = false;
      })
      .then(() => {
        getFileList({
          fid: paths2.value[paths2.value.length - 1]?.fid ?? '0',
        });
      });
  } else if (props.item?.cloudType === 'tianyiyun') {
    loading.value = true;
    await deleteCloud189FileApi({
      file_ids: [
        {
          fileId: _file.fid,
          fileName: _file.file_name,
          isFolder: _file.dir ? 1 : 0,
        },
      ],
    })
      .finally(() => {
        loading.value = false;
      })
      .then(() => {
        getFileList({
          fid: paths2.value[paths2.value.length - 1]?.fid ?? '-11',
        });
      });
  }
};
</script>

<template>
  <Modal
    v-model:open="open"
    :title="modalTitle"
    :width="width"
    destroy-on-close
  >
    <div v-loading="loading" v-show="currentStep === 0">
      <FolderSelect
        v-model:selected-file="selectedFile"
        :file-list="fileList"
        :paths="paths"
        @navigate-to="navigateTo"
      />
    </div>
    <div v-loading="loading" v-show="currentStep === 1">
      <FolderSelect
        :if-use-checkbox="false"
        :file-list="fileList2"
        :paths="paths2"
        :if-use-file-manager="true"
        @navigate-to="navigateTo"
        @create-dir="createDir"
        @rename="rename"
        @delete="deleteFile"
      />
    </div>
    <template #footer>
      <Button @click="onBack" v-show="currentStep === 1"> 返回 </Button>
      <Button type="primary" @click="onOk">{{ okText }}</Button>
    </template>
  </Modal>
</template>