from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class PostsViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Test_title',
            description='Test_description',
            slug='Group',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

        cls.url_index = reverse('posts:index')
        cls.url_post_create = reverse('posts:post_create')
        cls.url_post_edit = reverse(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )

        cls.url_group_posts = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.url_profile = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username}
        )
        cls.url_post_detail = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.unauthorized_client = Client()

        self.authorized_client.force_login(PostsViewsTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls_names = {
            'posts/index.html': PostsViewsTest.url_index,
            'posts/post_create.html': PostsViewsTest.url_post_create,
            'posts/group_list.html': PostsViewsTest.url_group_posts,
            'posts/profile.html': PostsViewsTest.url_profile,
            'posts/post_detail.html': PostsViewsTest.url_post_detail
        }

        for template, address in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def page_obj(self, address):
        """Проверка переменной page_obj"""
        response = self.authorized_client.get(address)
        self.assertIn('page_obj', response.context)
        post = response.context['page_obj'][0]
        self.assertEqual(post.author, PostsViewsTest.user)
        self.assertEqual(post.text, PostsViewsTest.post.text)
        self.assertEqual(post.group, PostsViewsTest.group)

    def test_context_index_page(self):
        """Тест, проверяющий контекст из response"""
        self.page_obj(PostsViewsTest.url_index)

    def test_context_group_posts(self):
        """Тест, проверяющий контекст cтраницы group_posts"""
        self.page_obj(PostsViewsTest.url_group_posts)

        response = self.unauthorized_client.get(PostsViewsTest.url_group_posts)
        group = response.context['group']

        self.assertEqual(PostsViewsTest.group.title, group.title)
        self.assertEqual(
            PostsViewsTest.group.description, group.description
        )
        self.assertEqual(PostsViewsTest.group.slug, group.slug)

    def test_context_profile(self):
        """Тест, проверяющий контекст cтраницы profile"""
        self.page_obj(PostsViewsTest.url_profile)

        response = self.authorized_client.get(PostsViewsTest.url_profile)
        author = response.context['author']
        post = response.context['post']

        self.assertEqual(author, PostsViewsTest.user)
        self.assertEqual(len(post), 1)

    def test_context_post_detail(self):
        """Тест, проверяющий контекст cтраницы post_detail"""
        response = self.unauthorized_client.get(PostsViewsTest.url_post_detail)
        author = response.context['author']
        post = response.context['post']
        count = response.context['posts_count']

        self.assertEqual(author, PostsViewsTest.user)
        self.assertEqual(post.text, PostsViewsTest.post.text)
        self.assertEqual(count, PostsViewsTest.post.author.post.count())

    def test_context_post_create(self):
        """Тест, проверяющий контекст cтраницы post_create"""
        response = self.authorized_client.get(PostsViewsTest.url_post_create)

        dict_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }

        for value, expected in dict_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_context_post_edit(self):
        """Тест, проверяющий контекст cтраницы post_edit"""
        response = self.authorized_client.get(PostsViewsTest.url_post_edit)

        dict_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }

        for value, expected in dict_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)
        self.assertIsInstance(is_edit, bool)

        post = response.context.get('post')
        post_count = response.context['post'].author.post.count()
        self.assertEqual(post.text, PostsViewsTest.post.text)
        self.assertEqual(post.pub_date, PostsViewsTest.post.pub_date)
        self.assertEqual(post.author, PostsViewsTest.post.author)
        self.assertEqual(post_count, PostsViewsTest.post.author.post.count())

    def test_correct_views_group(self):
        """Тест, проверяющий корректность отображения новой группы"""
        self.new_group = Group.objects.create(
            title='Test_title_new',
            description='Test_description_new',
            slug='Group_new',
        )
        self.url_group_posts_new = reverse(
            'posts:group_list',
            kwargs={'slug': self.new_group.slug}
        )
        response = self.authorized_client.get(self.url_group_posts_new)
        group = response.context.get('group')
        self.assertEqual(group.title, self.new_group.title)
        self.assertEqual(group.description, self.new_group.description)
        self.assertEqual(group.slug, self.new_group.slug)

    def test_paginator(self):
        """Тест, проверяющий работу пагинатора"""
        paginator_amount = 10
        all_posts_count = 14

        posts = [
            Post(
                text=f'test text {1+num}', author=PostsViewsTest.user,
                group=PostsViewsTest.group
            ) for num in range(all_posts_count)
        ]
        Post.objects.bulk_create(posts)
        pages = (
            (1, paginator_amount),
            (2, all_posts_count - paginator_amount + 1)
        )

        for page, count in pages:
            response = self.unauthorized_client.get(
                PostsViewsTest.url_index, {'page': page}
            )

            self.assertEqual(
                len(response.context.get('page_obj').object_list), count
            )


class CacheIndexTest(TestCase):
    @classmethod
    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.group = Group.objects.create(
            title='Test_title',
            description='Test_description',
            slug='Group',
        )
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )

        self.url_index = reverse('posts:index')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        response = self.authorized_client.get(self.url_index)
        self.post.delete()
        response_cache = self.authorized_client.get(self.url_index)
        self.assertEqual(response.content, response_cache.content)
        cache.clear()
        response_clear = self.authorized_client.get(self.url_index)
        self.assertNotEqual(response_clear.content, response)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_2 = User.objects.create_user(username='test_user_2')
        cls.user_3 = User.objects.create_user(username='test_user_3')
        cls.group = Group.objects.create(
            title='Test_title',
            description='Test_description',
            slug='Group',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

        cls.index = reverse('posts:follow_index')
        cls.profile_follow = reverse(
            'posts:profile_follow', kwargs={'username': cls.user.username}
        )

        cls.profile_unfollow = reverse(
            'posts:profile_unfollow', kwargs={'username': cls.user.username}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.unauthorized_client = Client()
        self.authorized_client_2 = Client()

        self.authorized_client.force_login(FollowTest.user_2)
        self.authorized_client_2.force_login(FollowTest.user_3)

    def test_profile_follow(self):
        count = Follow.objects.count()
        response_follow = self.authorized_client.get(
            FollowTest.profile_follow, follow=True
        )

        self.assertEqual(response_follow.status_code, HTTPStatus.OK)
        self.assertEqual(Follow.objects.count(), count + 1)
        self.assertRedirects(response_follow, '/profile/test_user/')

        response_unfollow = self.authorized_client.get(
            FollowTest.profile_unfollow, follow=True
        )

        self.assertEqual(response_unfollow.status_code, HTTPStatus.OK)
        self.assertEqual(Follow.objects.count(), count)
        self.assertRedirects(response_unfollow, '/profile/test_user/')

    def test_index_follow(self):
        response_follow = self.authorized_client.get(
            FollowTest.profile_follow, follow=True
        )
        response = self.authorized_client.get(FollowTest.index)
        response_2 = self.authorized_client_2.get(FollowTest.index)
        Post.objects.create(
            text='new_text',
            author=FollowTest.user
        )
        resoponse_3 = self.authorized_client.get(FollowTest.index)
        resoponse_4 = self.authorized_client_2.get(FollowTest.index)

        self.assertNotEqual(response.content, resoponse_3.content)
        self.assertEqual(response_2.content, resoponse_4.content)
        self.assertEqual(response_follow.status_code, HTTPStatus.OK)
