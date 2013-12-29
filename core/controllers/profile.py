# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Controllers for the profile page."""

__author__ = 'sfederwisch@google.com (Stephanie Federwisch)'

from core.controllers import base
from core.domain import config_domain
from core.domain import exp_services
from core.domain import stats_services
from core.domain import user_services
import feconf
import utils

import jinja2


EDITOR_PREREQUISITES_AGREEMENT = config_domain.ConfigProperty(
    'editor_prerequisites_agreement', 'UnicodeString',
    'The agreement that editors are asked to accept before making any '
    'contributions.',
    default_value=feconf.DEFAULT_EDITOR_PREREQUISITES_AGREEMENT
)


class ProfilePage(base.BaseHandler):
    """The profile page."""

    PAGE_NAME_FOR_CSRF = 'gallery_or_profile'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        self.render_template('profile/profile.html')


class ProfileHandler(base.BaseHandler):
    """Provides data for the profile gallery."""

    @base.require_user
    def get(self):
        """Handles GET requests."""
        exps = exp_services.get_editable_explorations(self.user_id)

        # Make each entry of the category list unique.
        category_list = list(set([exp.category for exp in exps]))

        self.values.update({
            'explorations': [{
                'id': exp.id,
                'name': exp.title,
            } for exp in exps],
            'improvable': stats_services.get_top_improvable_states(
                [exp.id for exp in exps], 10),
            'category_list': list(category_list)
        })
        self.render_json(self.values)


class EditorPrerequisitesPage(base.BaseHandler):
    """The page which prompts for username and acceptance of terms."""

    PAGE_NAME_FOR_CSRF = 'editor_prerequisites_page'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        self.values.update({
            'agreement': EDITOR_PREREQUISITES_AGREEMENT.value,
        })
        self.render_template('profile/editor_prerequisites.html')


class EditorPrerequisitesHandler(base.BaseHandler):
    """Provides data for the editor prerequisites page."""

    PAGE_NAME_FOR_CSRF = 'editor_prerequisites_page'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        user_settings = user_services.get_user_settings(self.user_id)
        self.render_json({
            'username': user_settings.username,
            'has_agreed_to_terms': bool(user_settings.last_agreed_to_terms),
        })

    @base.require_user
    def post(self):
        """Handles POST requests."""
        username = self.payload.get('username')
        agreed_to_terms = self.payload.get('agreed_to_terms')

        if not isinstance(agreed_to_terms, bool) or not agreed_to_terms:
            raise self.InvalidInputException(
                'In order to edit explorations on this site, you will '
                'need to accept the license terms.')
        else:
            user_services.record_agreement_to_terms(self.user_id)

        if user_services.get_username(self.user_id):
            # A username has already been set for this user.
            self.render_json({})
            return

        try:
            user_services.set_username(self.user_id, username)
        except utils.ValidationError as e:
            raise self.InvalidInputException(e)

        self.render_json({})
