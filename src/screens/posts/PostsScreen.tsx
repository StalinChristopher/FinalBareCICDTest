import { DrawerActions } from '@react-navigation/native';
import React from 'react';
import { useTranslation } from 'react-i18next';
import { FlatList, StyleSheet, Text, View } from 'react-native';

import type { Post } from '../../api/types/api';
import { TopBar } from '../../components/TopBar';
import { APP_DISPLAY_NAME } from '../../config/appDisplayName';
import type { PostsMainCompositeProps } from '../../navigation/screenTypes';
import { useAppQuery } from '../../query/hooks/useAppQuery';
import { postService } from '../../services/postService';
import { useThemedStyles } from '../../theme/useThemedStyles';

type Props = PostsMainCompositeProps;

const PostsScreen = ({ navigation }: Props) => {
  const { t } = useTranslation();
  const {
    data: posts,
    isPending,
    error,
  } = useAppQuery(['posts'], () => postService.getPosts());

  const styles = useThemedStyles(
    colors => ({
      root: { flex: 1, backgroundColor: colors.background },
      container: {
        flex: 1,
        padding: 16,
        backgroundColor: colors.background,
        paddingTop: 16,
      },
      centered: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
        backgroundColor: colors.background,
      },
      title: {
        fontSize: 22,
        fontWeight: '700',
        marginBottom: 12,
        color: colors.text1,
      },
      row: {
        paddingVertical: 12,
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderBottomColor: colors.grayBackground,
      },
      rowTitle: { fontSize: 16, fontWeight: '600', color: colors.text1 },
      rowBody: {
        fontSize: 14,
        opacity: 0.75,
        marginTop: 4,
        color: colors.text2,
      },
      empty: {
        textAlign: 'center',
        marginTop: 24,
        opacity: 0.6,
        color: colors.text3,
      },
      error: { color: colors.error, textAlign: 'center' },
      loadingText: { color: colors.text2 },
    }),
    [],
  );

  const openMenu = () => navigation.dispatch(DrawerActions.openDrawer());

  const menuBar = (
    <TopBar topBarTitle={APP_DISPLAY_NAME} onMenuPress={openMenu} />
  );

  if (isPending) {
    return (
      <View style={styles.root}>
        {menuBar}
        <View style={styles.centered}>
          <Text style={styles.loadingText}>{t('posts.loading')}</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.root}>
        {menuBar}
        <View style={styles.centered}>
          <Text style={styles.error}>{error.message}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.root}>
      {menuBar}
      <View style={styles.container}>
        <Text style={styles.title}>{t('posts.title')}</Text>
        <FlatList<Post>
          data={posts ?? []}
          keyExtractor={item => String(item.id)}
          renderItem={({ item }) => (
            <View style={styles.row}>
              <Text style={styles.rowTitle}>{item.title}</Text>
              <Text style={styles.rowBody} numberOfLines={2}>
                {item.body}
              </Text>
            </View>
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>{t('posts.empty')}</Text>
          }
        />
      </View>
    </View>
  );
};

export default PostsScreen;
