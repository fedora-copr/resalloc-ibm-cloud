%global desc %{expand:
Helper scripts for the Resalloc server (mostly used by Copr build system)
for maintaining VMs in IBM Cloud (starting, stopping, cleaning orphans, etc.).
}

Name:           resalloc-ibm-cloud
Version:        1.0.0
Release:        %autorelease
Summary:        Resource allocator scripts for IBM cloud

License:        GPLv2+
URL:            https://github.com/fedora-copr/%{name}
Source0:        %{url}/archive/refs/tags/%{name}-%{version}.tar.gz


BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-ibm-vpc
BuildRequires:  python3-ibm-cloud-sdk-core
BuildRequires:  pyproject-rpm-macros


%description
%{desc}


%prep
%autosetup -n %{name}-%{version}


%generate_buildrequires
%pyproject_buildrequires -r


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files resalloc_ibm_cloud


%files -n %{name} -f %{pyproject_files}
%license LICENSE
%doc README.md
%{_bindir}/resalloc-ibm-cloud-list-deleting-vms
%{_bindir}/resalloc-ibm-cloud-list-vms
%{_bindir}/resalloc-ibm-cloud-vm


%changelog
%autochangelog
