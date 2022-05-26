import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
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

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.unauthorized_client = Client()

        self.authorized_client.force_login(PostsFormsTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_urls_names = {
            'posts/index.html': PostsFormsTest.url_index,
            'posts/post_create.html': PostsFormsTest.url_post_create,
            'posts/group_list.html': PostsFormsTest.url_group_posts,
            'posts/profile.html': PostsFormsTest.url_profile,
            'posts/post_detail.html': PostsFormsTest.url_post_detail
        }

        for template, address in templates_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create(self):
        """Валидная форма создает запись."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        self.url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostsFormsTest.user.username}
        )
        post_data = {
            'text': 'new_text', 'group': PostsFormsTest.group.pk,
            'image': uploaded}

        response_one = self.authorized_client.post(
            reverse('posts:post_create'), post_data, follow=True
        )

        self.assertEqual(response_one.status_code, HTTPStatus.OK)
        self.assertRedirects(response_one, self.url_profile)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.first()
        self.assertEqual(post.text, post_data['text'])
        self.assertEqual(post.group.pk, post_data['group'])
        self.assertEqual(post.image, 'posts/small.gif')

        urls_pages = [
            PostsFormsTest.url_index,
            PostsFormsTest.url_group_posts,
            PostsFormsTest.url_post_detail,
            PostsFormsTest.url_profile
        ]

        for url in urls_pages:
            with self.subTest(url=url):
                response_two = self.authorized_client.get(url)
                self.assertEqual(response_two.status_code, HTTPStatus.OK)
                self.assertEqual(post.image, 'posts/small.gif')

    def test_post_edit(self):
        """Валидная форма редактирует запись."""
        post_data = {'text': 'text_edit', 'group': PostsFormsTest.post.id}

        response = self.authorized_client.post(
            PostsFormsTest.url_post_edit, post_data
        )

        post = Post.objects.first()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post.text, post_data['text'])
        self.assertRedirects(response, PostsFormsTest.url_post_detail)

    def test_comment_authorized_user(self):
        """Посты может комментировать только авторизированный пользователь."""
        comment_count = Comment.objects.count()
        self.url_add_comment = reverse(
            'posts:add_comment', kwargs={'post_id': PostsFormsTest.post.pk}
        )
        data_comment = {
            'author': PostsFormsTest.user,
            'post': PostsFormsTest.post,
            'text': 'text_comment',
        }
        response = self.authorized_client.post(
            self.url_add_comment, data=data_comment, follow=True
        )

        comment = Comment.objects.first()
        self.assertRedirects(response, PostsFormsTest.url_post_detail)
        self.assertEqual(comment.post, data_comment['post'])
        self.assertEqual(comment.author, data_comment['author'])
        self.assertEqual(comment.text, data_comment['text'])
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_comment_unauthorized_user(self):
        """Посты не может комментировать неавторизированный пользователь."""
        comment_count = Comment.objects.count()
        self.url_add_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': PostsFormsTest.post.id}
        )
        data_comment = {'text': 'text_comment',
                        'author': PostsFormsTest.user.pk,
                        'post': PostsFormsTest.post.pk
                        }
        response = self.unauthorized_client.post(
            self.url_add_comment, data=data_comment, follow=True
        )

        self.assertRedirects(response, '/auth/login/?next=/posts/1/comment/')
        self.assertEqual(Comment.objects.count(), comment_count)
