from scanner.base import BaseCheck, CheckResult


class SecurityGroupsCheck(BaseCheck):
    check_id = "security_groups"
    severity = "high"

    def run(self, session) -> list[CheckResult]:
        client = session.client("ec2")
        sgs = client.describe_security_groups().get("SecurityGroups", [])
        results = []
        dangerous_ports = {22, 3389, 3306, 5432, 1433, 27017, 6379, 9200, 11211}
        for sg in sgs:
            sg_id = sg["GroupId"]
            sg_name = sg.get("GroupName", "unknown")
            open_rules = []
            for rule in sg.get("IpPermissions", []):
                is_all_traffic = rule.get("IpProtocol") == "-1"
                from_port = rule.get("FromPort") if not is_all_traffic else 0
                to_port = rule.get("ToPort") if not is_all_traffic else 65535
                # Default to full range if ports not specified
                if from_port is None:
                    from_port = 0
                if to_port is None:
                    to_port = 65535

                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        if is_all_traffic:
                            open_rules.append("ALL traffic")
                        else:
                            for port in dangerous_ports:
                                if from_port <= port <= to_port:
                                    open_rules.append(f"port {port}")
                for ip_range in rule.get("Ipv6Ranges", []):
                    if ip_range.get("CidrIpv6") == "::/0":
                        if is_all_traffic:
                            open_rules.append("ALL traffic (IPv6)")
                        else:
                            for port in dangerous_ports:
                                if from_port <= port <= to_port:
                                    open_rules.append(f"port {port} (IPv6)")
            if open_rules:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Security group '{sg_name}' has unrestricted access",
                        status="fail",
                        severity=self.severity,
                        message=f"Security group {sg_id} allows unrestricted ingress on: {', '.join(set(open_rules))}.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Restrict ingress rules on security group '{sg_name}'.",
                        remediation_steps=[
                            f"Open EC2 console > Security Groups > {sg_id}",
                            "Edit inbound rules",
                            "Replace 0.0.0.0/0 with specific IP ranges",
                            "Remove unnecessary port access",
                        ],
                        resource=f"Security Group: {sg_id} ({sg_name})",
                        domain=self.domain,
                        resource_type="EC2",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Security group '{sg_name}' is properly configured",
                        status="pass",
                        severity=self.severity,
                        message=f"Security group {sg_id} does not allow unrestricted access to sensitive ports.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=f"Security Group: {sg_id} ({sg_name})",
                        domain=self.domain,
                        resource_type="EC2",
                    )
                )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No security groups found",
                    status="pass",
                    severity=self.severity,
                    message="No security groups found to check.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="EC2",
                    domain=self.domain,
                    resource_type="EC2",
                )
            )
        return results


class VPCFlowLogsCheck(BaseCheck):
    check_id = "vpc_flow_logs"
    severity = "medium"

    def run(self, session) -> list[CheckResult]:
        client = session.client("ec2")
        vpcs = client.describe_vpcs().get("Vpcs", [])
        results = []
        for vpc in vpcs:
            vpc_id = vpc["VpcId"]
            flow_logs = client.describe_flow_logs(
                Filters=[{"Name": "resource-id", "Values": [vpc_id]}]
            ).get("FlowLogs", [])
            if flow_logs:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"Flow logs enabled on VPC {vpc_id}",
                        status="pass",
                        severity=self.severity,
                        message=f"VPC {vpc_id} has flow logs enabled for network monitoring.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        resource=f"VPC: {vpc_id}",
                        domain=self.domain,
                        resource_type="EC2",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        check_id=self.check_id,
                        title=f"No flow logs on VPC {vpc_id}",
                        status="fail",
                        severity=self.severity,
                        message=f"VPC {vpc_id} does not have flow logs enabled.",
                        nis2_article=self.nis2_article,
                        nis2_requirement=self.nis2_requirement,
                        remediation=f"Enable VPC flow logs on {vpc_id}.",
                        remediation_steps=[
                            f"Open VPC console > {vpc_id} > Flow Logs",
                            "Click 'Create flow log'",
                            "Set filter to 'All'",
                            "Choose CloudWatch Logs or S3 as destination",
                            "Create the flow log",
                        ],
                        resource=f"VPC: {vpc_id}",
                        domain=self.domain,
                        resource_type="EC2",
                    )
                )
        if not results:
            results.append(
                CheckResult(
                    check_id=self.check_id,
                    title="No VPCs found",
                    status="pass",
                    severity=self.severity,
                    message="No VPCs found to check.",
                    nis2_article=self.nis2_article,
                    nis2_requirement=self.nis2_requirement,
                    resource="VPC",
                    domain=self.domain,
                    resource_type="EC2",
                )
            )
        return results
