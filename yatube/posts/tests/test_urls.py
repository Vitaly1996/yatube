from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from http import HTTPStatus


from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_index_page(self):
        '''Проверка доступности адреса /.'''
        response = self.guest_client.get('/')

        self.assertEqual(response.status_code, 200)


class PostsURLTest(TestCase):
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
            'posts:post_edit',
            kwargs={'post_id': 1}
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
            'posts:post_detail', kwargs={'post_id': 1}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.unauthorized_client = Client()

        self.authorized_client.force_login(PostsURLTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls_names = {
            'posts/index.html': PostsURLTest.url_index,
            'posts/post_create.html': PostsURLTest.url_post_create,
            'posts/group_list.html': PostsURLTest.url_group_posts,
            'posts/profile.html': PostsURLTest.url_profile,
            'posts/post_detail.html': PostsURLTest.url_post_detail
        }
        for template, address in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_public_pages(self):
        """Проверка общедоступных страниц"""
        url_public_pages = [
            PostsURLTest.url_index,
            PostsURLTest.url_group_posts,
            PostsURLTest.url_profile,
            PostsURLTest.url_post_detail
        ]
        for url in url_public_pages:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_access_author(self):
        """Проверка доступа страницы для автора"""
        response = self.authorized_client.get(PostsURLTest.url_post_edit)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_access_auth_client(self):
        """Проверка доступа страницы для aвторизированного пользователя"""
        response = self.authorized_client.get(PostsURLTest.url_post_create)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_redirect_anonymous_on_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу /auth/login/?next=/create/"""
        response = self.unauthorized_client.get(PostsURLTest.url_post_create)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page(self):
        """Проверка доступа к несуществующей странице"""
        response = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
