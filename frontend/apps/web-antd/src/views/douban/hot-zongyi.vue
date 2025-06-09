<script setup lang="ts">
import { getHotMovieListApi } from './api';
import MediaCardList from './components/MediaCardList.vue';
</script>
<template>
  <div>
    <MediaCardList
      :api="getHotMovieListApi"
      :params="{ type: 'tv', category: 'show' }"
    />
  </div>
</template>
