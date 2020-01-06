import os

from bsd import geom
from copy import deepcopy

from middlewared.service import CallError, Service
from middlewared.utils import filter_list, run

from .mirror_base import DiskMirrorBase


class DiskService(Service, DiskMirrorBase):

    async def create_mirror(self, name, options):
        cp = await run('gmirror', 'create', name, *(options['paths']), check=False, encoding='utf8')
        if cp.returncode:
            raise CallError('Failed to create gmirror %s: %s', name, cp.stderr)

    async def destroy_mirror(self, name):
        mirror_data = await self.middleware.call('disk.get_mirrors', [['name', '=', name]], {'get': True})
        mirror_name = os.path.join('mirror', name)
        if mirror_data['encrypted_path']:
            await self.middleware.call('disk.remove_encryption', f'{mirror_name}.eli')

        cp = await run('gmirror', 'destroy', mirror_name, check=False, encoding='utf8')
        if cp.returncode:
            raise CallError('Failed to destroy mirror %s: %s', mirror_name, cp.stderr)

    def get_mirrors(self, filters, options):
        mirrors = []
        geom.scan()
        klass = geom.class_by_name('MIRROR')
        if not klass:
            return mirrors
        for g in klass.geoms:
            mirror_data = {
                **deepcopy(self.mirror_base),
                'name': g.name,
                'config_type': g.config.get('Type') if g.config else None,
                'path': os.path.join('/dev/mirror', g.name),
                'real_path': os.path.join('/dev/mirror', g.name),
            }
            if os.path.exists(f'{mirror_data["path"]}.eli'):
                mirror_data['encrypted_path'] = f'{mirror_data["path"]}.eli'
            for c in g.consumers:
                mirror_data['providers'].append({
                    'name': c.provider.name, 'id': c.provider.id, 'disk': c.provider.geom.name
                })
            mirrors.append(mirror_data)

        return filter_list(mirrors, filters, options)