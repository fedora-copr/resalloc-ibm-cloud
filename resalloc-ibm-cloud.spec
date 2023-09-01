%global desc %{expand:
Helper scripts for the Resalloc server (mostly used by Copr build system)
for maintaining VMs in IBM Cloud (starting, stopping, cleaning orphans, etc.).
}

Name:           resalloc-ibm-cloud
Version:        0.1.0
Release:        1%{?dist}
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

mkdir -p  %buildroot%_mandir/man1
install  -p -m 644 man/*.1 %buildroot%_mandir/man1


%files -n %{name} -f %{pyproject_files}
%license LICENSE
%doc README.md
%_mandir/man1/resalloc-ibm-cloud*1*
%{_bindir}/ibm-cloud-list-deleting-vms
%{_bindir}/ibm-cloud-list-vms
%{_bindir}/ibm-cloud-vm


%changelog
* Wed Jan 18 2023 Jiri Kyjovsky <j1.kyjovsky@gmail.com>
- Initial package.
