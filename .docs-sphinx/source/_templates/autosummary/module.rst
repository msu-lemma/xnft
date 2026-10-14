{{ fullname }}
{{ "=" * fullname|length }}

.. automodule:: {{ fullname }}
   :no-members:
   :no-inherited-members:

{% if modules %}
Submodules
----------

.. autosummary::
   :toctree:
   :recursive:
   :nosignatures:

{% for item in modules %}
   {{ item }}
{% endfor %}
{% endif %}

{% if functions %}
Functions
---------

.. autosummary::
   :toctree:
   :nosignatures:

{% for item in functions %}
   {{ item }}
{% endfor %}
{% endif %}

{% if classes %}
Classes
-------

.. autosummary::
   :toctree:
   :nosignatures:

{% for item in classes %}
   {{ item }}
{% endfor %}
{% endif %}
